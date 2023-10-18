#!/usr/bin/env bash

# This script sets up an EC2 instance for airbridge.
# Project website: https://github.com/openbridge/airbridge

readonly MARKER_FILE="/etc/user_data_marker"
readonly LOG_FILE="/var/log/script_execution.log"

# Logs messages to a defined log file.
# Globals:
#   LOG_FILE: Path to the log file.
# Arguments:
#   msg: Message to log.
# Returns:
#   None
log() {
    local msg="$1"
    echo "$(date): ${msg}" | tee -a "${LOG_FILE}"
}

# Handles errors by logging them and then exiting.
# Globals:
#   LOG_FILE: Path to the log file.
# Arguments:
#   msg: Error message.
# Returns:
#   None
handle_error() {
    local msg="$1"
    echo "Error: ${msg}" >&2 | tee -a "${LOG_FILE}"
    exit 1
}

# Sets an environment variable in /etc/environment.
# Arguments:
#   key: Environment variable key.
#   value: Environment variable value.
# Returns:
#   None
set_environment_variable() {
    local env_file="/etc/environment"
    local backup_file="${env_file}.bak"
    local key="$1"
    local value="$2"

    # Check if the environment file exists and is writable
    if [[ ! -w "${env_file}" ]]; then
        handle_error "Error: ${env_file} does not exist or is not writable." 
    fi

    # Backup the original environment file
    cp "${env_file}" "${backup_file}"

    # Check if the key already exists in the file
    if grep -q "^${key}=" "${env_file}"; then
        sed -i "s|^${key}=.*|${key}=\"${value}\"|" "${env_file}"
    else
        echo "${key}=\"${value}\"" >>"${env_file}"
    fi
}


# Update system packages.
# Returns:
#   None
update_system() {
    yum update -y || handle_error "Failed to update system packages."
}

# Install necessary packages.
# Returns:
#   None
install_packages() {
    yum install -y amazon-cloudwatch-agent cronie docker gcc git openssl pip python python3-devel || handle_error "Failed to install yum packages."
}

# Starts and enables necessary services.
# Returns:
#   None
start_services() {
    # Start and enable Docker service
    if ! service docker start; then
        handle_error "Failed to start docker service."
    fi

    if ! systemctl enable docker; then
        handle_error "Failed to enable docker service."
    fi

    local docker_status
    docker_status=$(systemctl is-enabled docker)
    if [[ "${docker_status}" != "enabled" ]]; then
        handle_error "Docker service is not enabled."
    fi

    docker_status=$(systemctl is-active docker)
    if [[ "${docker_status}" != "active" ]]; then
        handle_error "Docker service is not running."
    fi

    # Start and enable crond service
    if ! systemctl start crond; then
        handle_error "Failed to start crond service."
    fi

    if ! systemctl enable crond; then
        handle_error "Failed to enable crond service."
    fi

    local crond_status
    crond_status=$(systemctl is-enabled crond)
    if [[ "${crond_status}" != "enabled" ]]; then
        handle_error "crond service is not enabled."
    fi

    crond_status=$(systemctl is-active crond)
    if [[ "${crond_status}" != "active" ]]; then
        handle_error "crond service is not running."
    fi
}

# Adds ec2-user to the docker group.
# Returns:
#   None
add_to_docker_group() {
    if ! usermod -a -G docker ec2-user; then
        handle_error "Failed to add ec2-user to docker group."
    fi
}

# Installs Python packages.
# Returns:
#   None
install_python_packages() {
    if ! pip install --ignore-installed docker boto3 psutil croniter Jinja2 filelock awscli; then
        handle_error "Failed to install Python packages."
    fi
}

# Retrieves EC2 metadata using a token.
# Arguments:
#   metadata_key: Metadata key to retrieve.
# Returns:
#   Retrieved metadata.
get_ec2_metadata() {
    local metadata_key="$1"
    local token
    token=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
    if [[ -z "${token}" ]]; then
        handle_error "Failed to retrieve token for EC2 metadata access. Ensure metadata is enabled."
    fi
    local response
    response=$(curl -s -H "X-aws-ec2-metadata-token: ${token}" "http://169.254.169.254/latest/meta-data/${metadata_key}")
    if [[ -z "${response}" ]]; then
        handle_error "Failed to retrieve EC2 metadata for key: ${metadata_key}. Ensure metadata is enabled."
    fi
    echo "${response}"
}

# Retrieves the EC2 instance ID.
# Returns:
#   Instance ID.
get_instance_id() {
    local instance_id
    instance_id=$(get_ec2_metadata "instance-id")
    echo "${instance_id}"
}

# Retrieves the current region of the EC2 instance.
# Returns:
#   Region of the EC2 instance.
get_region() {
    local availability_zone
    availability_zone=$(get_ec2_metadata "placement/availability-zone")
    local region
    region="${availability_zone%[a-z]}"
    echo "${region}"
}

# Clones the git repository and sets up the directories.
# Returns:
#   None
git_clone_and_setup() {
    local -r REPO_URL="https://github.com/openbridge/airbridge.git"
    local -r TMP_CLONE_DIR="/tmp/airbridge"
    local -r TARGET_DIR="/home/ec2-user/airbridge"
    
    # Export and set environment variable
    AIRBRIDGE_TARGET=${TARGET_DIR}
    set_environment_variable "AIRBRIDGE_TARGET" "${TARGET_DIR}"
    export AIRBRIDGE_TARGET

    # Ensure git is available
    if ! command -v git &> /dev/null; then
        handle_error "git could not be found."
    fi

    # Remove directories if they already exist
    [[ -d "${TMP_CLONE_DIR}" ]] && rm -Rf "${TMP_CLONE_DIR}"
    [[ -d "${AIRBRIDGE_TARGET}" ]] && rm -Rf "${AIRBRIDGE_TARGET}"
    
    # Clone the repository
    git clone "${REPO_URL}" "${TMP_CLONE_DIR}" || handle_error "Failed to clone repository."

    # Move the repository content to the target directory
    mv "${TMP_CLONE_DIR}/src/airbridge" "${AIRBRIDGE_TARGET}" || handle_error "Failed to move airbridge to target directory."

    # Create directories and set permissions
    mkdir -p "${AIRBRIDGE_TARGET}/secrets" "${AIRBRIDGE_TARGET}/output" || handle_error "Failed to create necessary directories."
    touch "${AIRBRIDGE_TARGET}/scheduler.log" || handle_error "Failed to create scheduler.log file."
    find "${AIRBRIDGE_TARGET}" -type d -exec chmod 755 {} \; || handle_error "Failed to set directory permissions."
    find "${AIRBRIDGE_TARGET}" -type f -exec chmod 644 {} \; || handle_error "Failed to set file permissions."

}


# Sets up AWS logs.
# Returns:
#   None
setup_aws_logs() {
    local -r INSTANCE_ID="$(get_instance_id)"
    local -r REGION_ID="$(get_region)"
    local -r CW_LOG_GROUP="airbridge-${INSTANCE_ID}"

    local existing_log_group
    existing_log_group=$(aws logs describe-log-groups --log-group-name-prefix "${CW_LOG_GROUP}" --query 'logGroups[?logGroupName==`'"${CW_LOG_GROUP}"'`].logGroupName' --output text --region "${REGION_ID}")

    if [[ "${existing_log_group}" == "${CW_LOG_GROUP}" ]]; then
        log "Log group ${CW_LOG_GROUP} already exists. Skipping creation."
    else
        aws logs create-log-group --log-group-name "${CW_LOG_GROUP}" --region "${REGION_ID}" || handle_error "Failed to create log group."
    fi

    local STREAM_NAME="airbridge-scheduler"
    local existing_log_stream
    existing_log_stream=$(aws logs describe-log-streams --log-group-name "${CW_LOG_GROUP}" --log-stream-name-prefix "${STREAM_NAME}" --query 'logStreams[?logStreamName==`'"${STREAM_NAME}"'`].logStreamName' --output text --region "${REGION_ID}")

    if [[ "${existing_log_stream}" == "${STREAM_NAME}" ]]; then
        log "Log stream ${STREAM_NAME} for ${CW_LOG_GROUP} already exists. Skipping creation."
    else
        aws logs create-log-stream --log-group-name "${CW_LOG_GROUP}" --log-stream-name "${STREAM_NAME}" --region "${REGION_ID}" || handle_error "Failed to create log stream."
    fi
}

# Checks for S3BUCKET environment variable or creates a new bucket.
# Returns:
#   None
setup_s3_bucket() {
    # If S3BUCKET is not set, attempt to create one
    if [[ -z "${S3BUCKET}" ]]; then
        log "S3BUCKET environment variable not set. Attempting to create or use a default bucket."
        
        local -r INSTANCE_ID="$(get_instance_id)"
        local -r REGION_ID="$(get_region)"
        S3BUCKET="airbridge-${INSTANCE_ID}"

        # Check if the S3 bucket exists
        if ! aws s3api head-bucket --bucket "${S3BUCKET}" &>/dev/null; then
            # Create the S3 bucket
            aws s3api create-bucket --bucket "${S3BUCKET}" --region "${REGION_ID}" || handle_error "Failed to create S3 bucket ${S3BUCKET}."
            log "Bucket ${S3BUCKET} created successfully."
        else
            log "Bucket ${S3BUCKET} already exists. Continuing..."
        fi

        # Set the S3BUCKET environment variable
        set_environment_variable "S3BUCKET" "${S3BUCKET}"
    fi

    # Double-check that the specified bucket exists or is accessible
    if ! aws s3api head-bucket --bucket "${S3BUCKET}" &>/dev/null; then
        handle_error "Bucket ${S3BUCKET} does not exist or you don't have permission to access it."
    fi

    # Construct and set the AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH environment variable
    AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH="s3://${S3BUCKET}/configs/scheduler.json"
    set_environment_variable "S3BUCKET" "${S3BUCKET}"
    set_environment_variable "AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH" "${AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH}"

    # Export the variable for current shell
    export AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH
    export S3BUCKET
}


# Creates the scheduler script that will be run using flock and cron.
# Globals:
#   AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH: The S3 path for the scheduler config.
#   AIRBRIDGE_TARGET: The target directory where the scheduler resides.
# Arguments:
#   None
# Returns:
#   None
create_scheduler_script() {
  local scheduler_script_path="/opt/run_scheduler.sh"

  # Ensure target directory exists
  [[ ! -d "/opt/" ]] && {
    mkdir -p "/opt/" || {
      echo "Failed to create directory /opt/" >&2
      return 1
    }
  }

  # Construct the scheduler script
  cat >"$scheduler_script_path" <<EOF
#!/usr/bin/env bash

# Set PATH variable to ensure all commands are available
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Exit immediately if a command exits with a non-zero status.
set -e

# Directory constants
readonly LOG_FILE="\${AIRBRIDGE_TARGET}/scheduler.log"
readonly PY_SCRIPT="\${AIRBRIDGE_TARGET}/scheduler.py"
readonly DB_PATH="\${AIRBRIDGE_TARGET}/scheduler.db"
readonly CONFIG_PATH="${AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH}"

# Change to the script's directory
cd "\${AIRBRIDGE_TARGET}" || {
  echo "Error: Failed to change directory to \${AIRBRIDGE_TARGET}" >&2
  exit 1
}

# Execute the Python script and log with timestamp
{
  echo "[\$(date '+%Y-%m-%d %H:%M:%S')] Starting scheduler script"
  python3 "\$PY_SCRIPT" --config="\$CONFIG_PATH" --db="\$DB_PATH"
  echo "[\$(date '+%Y-%m-%d %H:%M:%S')] Finished scheduler script"
} >> "\$LOG_FILE" 2>&1
EOF

  # Make the scheduler script executable
  chmod +x "$scheduler_script_path" || {
    echo "Failed to make $scheduler_script_path executable." >&2
    return 1
  }
}


# Backs up local files to S3 and cleans up local disk.
# Returns:
#   None
create_backup_script() {
    local -r BACKUP_SCRIPT_PATH="/opt/backup_to_s3.sh"

    # Ensure target directory exists
    if [[ ! -d "/opt/" ]]; then
        mkdir -p "/opt/" || {
            echo "Failed to create directory /opt/" >&2
            return 1
        }
    fi

    cat >"${BACKUP_SCRIPT_PATH}" <<EOF
#!/bin/bash

# This script backs up files from a local directory to an S3 bucket.

# Variables
LOCAL_DIR="${AIRBRIDGE_TARGET}/output"
S3_BUCKET="s3://${S3BUCKET}"

upload_to_s3() {
  local -r file_path="\$1"
  local -r relative_path="\${file_path#\$LOCAL_DIR/}"
  local -r s3_full_path="\$S3_BUCKET/\$relative_path"

  # Upload to S3 and check if the operation was successful
  if aws s3 cp "\$file_path" "\$s3_full_path"; then
    rm "\$file_path"
  else
    echo "Failed to upload \$file_path to S3" >&2
    return 1
  fi
}

find "\$LOCAL_DIR" -type f -mmin +60 -print | while read -r file; do
  upload_to_s3 "\$file"
done
EOF

    # Make the backup script executable
    chmod +x "${BACKUP_SCRIPT_PATH}" || {
        echo "Failed to make ${BACKUP_SCRIPT_PATH} executable." >&2
        return 1
    }
}

# Adds cron jobs for airbridge and backup scripts.
# Returns:
#   None
add_cron_job() {

    if [[ -z "${AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH}" ]]; then
        handle_error "AIRBRIDGE_SCHEDULER_CONFIG_S3_PATH is not set!"
    fi

    if [[ -z "${AIRBRIDGE_TARGET}" ]]; then
        handle_error "AIRBRIDGE_TARGET is not set!"
    fi

    local -r AIRBRIDGE_CRON_COMMAND="*/5 * * * * /usr/bin/flock -w 0 /tmp/scheduler.lock /opt/run_scheduler.sh"
    
    # Add AIRBRIDGE_CRON_COMMAND to crontab if it doesn't exist
    ( crontab -l 2>/dev/null | grep -v -F "${AIRBRIDGE_CRON_COMMAND}" ; echo "${AIRBRIDGE_CRON_COMMAND}" ) | crontab - || handle_error "Failed to add airbridge cron job."

    local -r BACKUP_SCRIPT_PATH="/opt/backup_to_s3.sh"
    local -r LOG_FILE_PATH="/var/log/backup_to_s3.log"
    local -r BACKUP_CRON_COMMAND="0 * * * * ${BACKUP_SCRIPT_PATH} >> ${LOG_FILE_PATH} 2>&1"
    
    # Add BACKUP_CRON_COMMAND to crontab if it doesn't exist
    ( crontab -l 2>/dev/null | grep -v -F "${BACKUP_CRON_COMMAND}" ; echo "${BACKUP_CRON_COMMAND}" ) | crontab - || handle_error "Failed to add backup_to_s3 cron job."
}


# Main function to orchestrate the setup.
# It updates the system, installs necessary packages, starts services, 
# sets up git repositories, configures s3 bucket, and creates backup scripts.
# Globals:
#   MARKER_FILE: File indicating the script has executed.
main() {
    update_system
    install_packages
    start_services
    add_to_docker_group
    install_python_packages
    git_clone_and_setup
    setup_s3_bucket
    setup_aws_logs
    create_scheduler_script
    create_backup_script
    add_cron_job

    # Creates a marker file to indicate the script has executed once.
    touch "${MARKER_FILE}"

    echo "Airbridge AWS install was successful!"
}

# Script's entry point.
main
