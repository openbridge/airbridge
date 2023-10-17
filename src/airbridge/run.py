#!/usr/bin/env python3

"""This script handles the initialization and execution of Airbyte.

It manages the necessary operations such as parsing arguments, managing Docker
containers, and coordinating Airbyte processes.
"""

# Standard library imports
import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass

from datetime import datetime

# Related third-party imports
import docker
from filelock import FileLock, Timeout

from state import main as state_main


# Constants
RUNTIME = "docker"  # Default runtime environment
DEFAULT_LOCK_FILE = (
    ".script.lock"  # Default lock file to prevent concurrent script executions
)
DEFAULT_TIMEOUT = 1  # Default timeout in seconds for acquiring the lock


src_runtime = int(datetime.now().timestamp())

# Initialize a logger for the script
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def src_config_md5(file_path: str) -> str:
    """Compute the MD5 hash of a given file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: MD5 hash of the file.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class LockManager:
    """A manager class for acquiring and releasing file-based locks.

    Attributes:
        lock_path (str): Path to the lock file.
        _has_lock (bool): Indicator if the lock is currently held.
        _file_lock (FileLock): File lock instance.

    Example Usage:
        with LockManager() as lock:
            # Protected code here.
            pass
    """

    def __init__(self, lock_path=None):
        """Initializes the LockManager with the provided lock path or the
        default path.

        Args:
            lock_path (str, optional): Path to the lock file. Defaults to the default lock file path.
        """
        self.lock_path = lock_path or self._get_default_lock_file_path()
        self._has_lock = False
        self._file_lock = FileLock(self.lock_path, timeout=DEFAULT_TIMEOUT)

    def _get_default_lock_file_path(self) -> str:
        """Returns the default lock file path based on the location of this
        script.

        Returns:doc
            str: Path to the default lock file.
        """
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), DEFAULT_LOCK_FILE
        )

    def __enter__(self):
        """Context manager entry method."""
        self.acquire_lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method."""
        if os.path.exists(".script.lock"):
            os.remove(".script.lock")
        self.release_lock()

    def acquire_lock(self):
        """Acquires the file lock."""
        try:
            self._file_lock.acquire()
            self._has_lock = True
        except Timeout:
            logger.warning(
                "Timeout occurred when trying to acquire lock for file %s.",
                self.lock_path,
            )
        except Exception:
            logger.exception("Unexpected error when trying to acquire lock.")
            raise

    def release_lock(self):
        """Releases the file lock if it's acquired."""
        if not self._has_lock:
            logger.warning(
                "Attempt to release a lock that was not acquired by this instance."
            )
            return

        try:
            self._file_lock.release()
            self._has_lock = False
        except Exception:
            logger.exception(
                "Error occurred while trying to release the lock."
            )
            raise


class ConfigManager:
    def __init__(self, default_config=None, config_file=None, cmd_args=None):
        """Initialize the ConfigManager with default configuration, a
        configuration file, and/or command line arguments.

        Args:
            default_config (dict, optional): Default configuration values. Defaults to None.
            config_file (str, optional): Path to a configuration file. Defaults to None.
            cmd_args (argparse.Namespace, optional): Command line arguments. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        self.config = default_config or {}

        if config_file:
            self._load_config_from_file(config_file)

        if cmd_args:
            self.update_from_args(cmd_args)

    def _load_config_from_file(self, config_path: str) -> None:
        """Load configurations from a file.

        Args:
            config_path (str): Path to the configuration file.
        """
        if not config_path:
            return

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                self.config.update(json.load(file))
        except FileNotFoundError:
            self.logger.error("Configuration file %s not found.", config_path)
        except json.JSONDecodeError:
            self.logger.error(
                "Error decoding JSON from configuration file %s.", config_path
            )
        except Exception as error:
            self.logger.error(
                "Unexpected error while reading configuration file %s: %s",
                config_path,
                error,
            )

    def update_from_args(self, cmd_args: argparse.Namespace) -> None:
        """Update configurations from command line arguments.

        Args:
            cmd_args (argparse.Namespace): Command line arguments.
        """
        self.config.update(vars(cmd_args))

class StateHandler:
    """A handler class for managing the execution of state scripts."""

    def __init__(
        self,
        output_path: str,
        airbyte_src_image: str,
        source_config_hash: str = None,
        job_id: str = None,
    ):
        """Initialize the StateHandler.

        Args:
            output_path (str): Path for output.
            airbyte_src_image (str): Airbyte source image.
            source_config_hash (str, optional): Hash of the source configuration. Defaults to None.
            job_id (str, optional): Job ID. Defaults to None.
        """
        self.output_path = output_path
        self.airbyte_src_image = airbyte_src_image
        self.job_id = job_id
        self.logger = logging.getLogger(__name__)
        self.source_config_hash = source_config_hash

    def run_state_script(self) -> bool:
        """Execute the state fetching and storing.

        Returns:
            bool: True if the state was fetched and stored successfully, False otherwise.
        """
        self.logger.info("Attempting to fetch and store state...")

        try:
            # Log that the state fetching and storing process has started
            self.logger.info("Starting state fetching and storing process...")
            
            state_main(
                src_runtime,
                self.output_path,
                "/home/ec2-user/airbridge",  # TODO: Parameterize this
                self.airbyte_src_image,
                self.job_id,
                self.source_config_hash,
            )
            
            # Log that the state fetching and storing process has completed
            self.logger.info("Completed state fetching and storing process successfully.")
            
            return True
        except FileNotFoundError:
            self.logger.error("State file not found.")
        except json.JSONDecodeError:
            self.logger.error("Error decoding JSON from state file.")
        except Exception as e:
            self.logger.exception(
                f"Unexpected error occurred while fetching and storing state: {e}"
            )
            return False


    def execute(self) -> None:
        """Execute the state-related actions."""
        success = self.run_state_script()
        if not success:
            # This log is optional, but if you want a specific log here, you can keep it
            self.logger.error("State action execution failed.")


class AirbyteDockerHandler:
    """Manages the execution of the state script for Airbyte operations."""

    def __init__(
        self,
        configuration: dict = None,
        output_path: str = None,
        src_image: str = None,
        dst_image: str = None,
        src_runtime=None,
    ):
        """Initialize the AirbyteDockerHandler.

        Args:
            configuration (dict, optional): A dictionary containing configuration settings. Defaults to None.
            output_path (str, optional): Path where output will be stored. Defaults to None.
            src_image (str, optional): Source Airbyte Docker image name. Defaults to None.
            dst_image (str, optional): Destination Airbyte Docker image name. Defaults to None.
            src_runtime ([type], optional): Source runtime. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        self.configuration = configuration or {}
        self.output_path = output_path
        self.src_image = src_image
        self.dst_image = dst_image
        self.job_id = self.configuration.get("job")
        self.src_runtime = src_runtime

        self.client = docker.from_env()  # Initialize the Docker client
        self.active_containers = []  # Initialize the active_containers attribute

        self.logger.info(
            "Source Image: %s, Destination Image: %s",
            self.src_image,
            self.dst_image,
        )

        if self.output_path:
            try:
                os.makedirs(self.output_path, exist_ok=True)
            except PermissionError:
                raise ValueError(
                    f"Permission denied when attempting to create the directory '{self.output_path}'."
                ) from None  # We might not want to chain this with the original exception
            except Exception as e:
                raise ValueError(
                    f"An error occurred while creating the directory '{self.output_path}': {e}"
                ) from e  # Explicitly chaining with the original exception


    # Airbyte-specific methods
    @staticmethod
    def sanitize_container_name(name: str) -> str:
        """Sanitize a container name to meet Docker's naming criteria. Replace
        any character not in [a-zA-Z0-9_.-] with an underscore.

        Args:
            name (str): The initial container name.

        Returns:
            str: A sanitized container name compliant with Docker's naming standards.
        """
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)

    def load_config_from_file(self, config_path: str) -> None:
        """Load configuration from a given file path and update the current
        configuration.

        Args:
            config_path (str): Path to the configuration file.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            json.JSONDecodeError: If there's an error decoding the JSON file.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                self.configuration.update(json.load(file))
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            self.logger.error(
                f"Error loading configuration from {config_path}: {e}"
            )

    def load_config_from_args(self, config_args) -> None:
        """Load configuration data from argparse arguments and update the
        instance's configuration.

        Args:
            config_args: Argument parser object containing the command-line arguments.
        """
        args_dict = vars(config_args)
        filtered_args = {
            k: v for k, v in args_dict.items() if not k.startswith("_")
        }
        self.configuration.update(filtered_args)

    def create_check_command(self) -> str:
        """Create a check command for Airbyte.

        Returns:
            str: The check command string.
        """
        return "check --config /secrets/config.json"

    # Docker helper methods

    def _initialize_docker_client(self) -> docker.DockerClient:
        """Initialize a Docker client. First, it tries to use environment
        variables. If that fails, it falls back to using the Docker socket
        directly.

        Returns:
            docker.DockerClient: Docker client instance.
        """
        try:
            client = docker.from_env()
            client.ping()
            return client
        except docker.errors.DockerException:
            return docker.DockerClient(base_url="unix://var/run/docker.sock")

    def check_docker_availability(self) -> bool:
        """Check if Docker is available and can be pinged.

        Returns:
            bool: True if Docker is available, False otherwise.
        """
        try:
            self.client.ping()
            return True
        except docker.errors.DockerException:
            self.logger.exception("Docker not available.")
            return False

    def check_image_provided(self, image, image_type: str):
        """Check if the given image is provided."""
        if not image:
            self.logger.error(f"{image_type} image is not provided.")
            return False
        return True

    def cleanup_container(self, container_name: str) -> bool:
        """Clean up and remove a specified Docker container.

        Args:
            container_name (str): Name of the Docker container.

        Returns:
            bool: True if cleanup was successful or container didn't exist, False otherwise.
        """
        try:
            container = self.client.containers.get(container_name)
            
            # If we reached this point, it means the container exists.
            #self.logger.info(f"Found an orphan container {container_name} that needs to be cleaned up.")
            
            container.remove(force=True)
            return True
        except docker.errors.NotFound:
            # No log or action needed if the container is not found.
            return True
        except docker.errors.APIError as api_err:
            self.logger.error(
                "API error cleaning up container %s: %s",
                container_name,
                api_err,
            )
            return False
        except Exception as general_error:
            self.logger.exception(
                "Error cleaning up container %s: %s",
                container_name,
                general_error,
            )
            return False


    def _common_volumes(self, mode: str, output_file_path: str = None) -> dict:
        """Generate common volume bindings based on the mode (source or
        destination) and output path."""
        volumes = {
            output_file_path: {"bind": "/tmp/", "mode": "rw"},
            self.configuration["catalog_loc"]: {
                "bind": "/secrets/catalog.json",
                "mode": "rw" if mode == "src" else "ro",
            },
            self.configuration[f"{mode}_config_loc"]: {
                "bind": "/secrets/config.json",
                "mode": "rw" if mode == "src" else "ro",
            },
        }
        return volumes

    def _prepare_volumes(self) -> tuple:
        src_volumes = self._common_volumes("src")
        dst_volumes = self._common_volumes("dst")
        src_volumes["/var/run/docker.sock"] = {
            "bind": "/var/run/docker.sock",
            "mode": "ro",
        }
        return src_volumes, dst_volumes

    def _prepare_src_volumes(self, output_file_path: str) -> dict:
        """Prepare source volumes including the state file if present.

        Args:
            output_file_path (str): Path for the output file.

        Returns:
            dict: Dictionary containing volume bindings for the source.
        """
        volumes = self._common_volumes("src", output_file_path)
        state_file_path = self.configuration.get("state_file_path")

        if state_file_path:
            self.logger.info(f"A state file was passed: {state_file_path}")

            if not os.path.exists(state_file_path):
                with open(
                    state_file_path, "w", encoding="utf-8"
                ) as state_file:
                    state_file.write("{}")  # Create an empty state file

            volumes[state_file_path] = {"bind": "/state.json", "mode": "rw"}

        return volumes

    def _prepare_dst_volumes(self, output_file_path: str) -> dict:
        """Prepare destination volumes.

        Args:
            output_file_path (str): Path for the output file.

        Returns:
            dict: Dictionary containing volume bindings for the destination.
        """
        return self._common_volumes("dst", output_file_path)

    def is_image_present(self, image_name: str, tag: str = None) -> bool:
        """Check if a specific Docker image with a given tag is present locally."""
        if not tag:
            # Check for both the image name alone (implying latest) and the explicit :latest tag
            return image_name in self.local_images or f"{image_name}:latest" in self.local_images
        else:
            return f"{image_name}:{tag}" in self.local_images

    @property
    def local_images(self):
        """List of locally available Docker images."""
        return [tag for img in self.client.images.list() for tag in img.tags]

    def pull_docker_image(self, image_name: str, tag: str = None) -> None:
        """... (rest of the docstring) ..."""
        
        if self.is_image_present(image_name, tag):
            self.logger.info(f"Image {image_name}:{tag if tag else 'latest'} is already present on the host. No need to pull.")
            return

        self.logger.info(f"Image {image_name}:{tag if tag else 'latest'} is not present locally. Initiating pull from Docker...")

        try:
            self.client.images.pull(image_name, tag=tag if tag else 'latest')
            self.logger.info(f"Successfully pulled Docker image {image_name}:{tag if tag else 'latest'}.")
        except docker.errors.ImageNotFound as exc:
            msg = f"Docker image {image_name}:{tag if tag else 'latest'} not found."
            self.logger.error(msg)
            raise DockerImageNotFoundError(msg) from exc
        except Exception as exc:
            msg = f"Unexpected error while pulling Docker image {image_name}:{tag if tag else 'latest'}. Error: {str(exc)}"
            self.logger.exception(msg)
            raise Exception(msg) from exc


    def run_image_check(self, image: str, volumes: dict) -> None:
        """Run a configuration check on the provided Docker image.

        Args:
            image (str): Docker image name.
            volumes (dict): Dictionary of volumes to bind to the container.

        Raises:
            Exception: If the image check fails.
        """
        image_name = image
        container_name = (
            self.sanitize_container_name(image) + "_clear" + str(uuid.uuid4())
        )
        # Log the info statement that a config check is about to start
        self.logger.info("Initiating config check for %s...", image)
        try:
            container = self.client.containers.run(
                image=image_name,
                entrypoint='bash -c "$AIRBYTE_ENTRYPOINT check --config /secrets/config.json"',
                volumes=volumes,
                detach=True,
                auto_remove=True,
                name=container_name,
            )
            self.active_containers.append(container_name)
            container.wait()
            self.logger.info("Config check for %s passed successfully.", image)
        except docker.errors.ContainerError as exc:
            self.logger.exception("Config check for %s failed", image)
            raise ConfigurationError(
                f"Configuration check for image {image} failed."
            ) from exc
        finally:
            # Cleanup the container after the check, irrespective of success or failure
            self.cleanup_container(container_name)

    def _run_container_with_entrypoint(
        self, image: str, entrypoint: str, volumes: dict, container_name: str
    ) -> None:
        """Run a Docker container with the specified entrypoint.

        Args:
            image (str): Docker image name.
            entrypoint (str): Entrypoint command for the Docker container.
            volumes (dict): Dictionary specifying volume bindings.
            container_name (str): Name for the Docker container.

        Raises:
            ContainerExecutionError: If there's an error while running the Docker container.
        """
        try:
            self.client.containers.run(
                image=image,
                entrypoint=entrypoint,
                volumes=volumes,
                detach=False,
                auto_remove=True,
                name=container_name,
            )
        except docker.errors.ContainerError as exc:
            self.logger.exception(
                "Error running Docker image %s with entrypoint %s",
                image,
                entrypoint,
            )
            raise ContainerExecutionError(
                f"Error running Docker image {image} with entrypoint {entrypoint}."
            ) from exc
        except Exception as exc:
            self.logger.exception(
                "Unexpected error while running Docker image %s with entrypoint %s",
                image,
                entrypoint,
            )
            raise ContainerExecutionError(
                f"Unexpected error while running Docker image {image}. Error: {str(exc)}"
            ) from exc

    def execute(
        self, src_airbyte_image: str = None, dst_airbyte_image: str = None
    ) -> bool:
        """Execute the Airbyte Docker images for source and destination.

        Args:
            src_airbyte_image (str, optional): Source Airbyte Docker image. Uses class attribute if not provided.
            dst_airbyte_image (str, optional): Destination Airbyte Docker image. Uses class attribute if not provided.

        Returns:
            bool: True if successful, False otherwise.
        """
        src_airbyte_image = src_airbyte_image or self.src_image
        if not self.check_image_provided(src_airbyte_image, "Source"):
            return False

        dst_airbyte_image = dst_airbyte_image or self.dst_image
        if not self.check_image_provided(dst_airbyte_image, "Destination"):
            return False

        run_time = math.ceil(time.time())
        output_file_path = os.path.join(
            self.output_path,
            src_airbyte_image.replace("/", "-"),
            str(run_time),
        )
        data_file = f"data_{self.src_runtime}.json"

        # Helper to construct source command
        def construct_src_command() -> str:
            command_base = "$AIRBYTE_ENTRYPOINT read --config /secrets/config.json --catalog /secrets/catalog.json"
            src_state_arg = (
                "--state /state.json"
                if self.configuration.get("state_file_path")
                else ""
            )
            return f'bash -c "{command_base} {src_state_arg} | tee /tmp/{data_file}"'

        # Helper to construct destination command
        def construct_dst_command() -> str:
            command_base = "$AIRBYTE_ENTRYPOINT write --config /secrets/config.json --catalog /secrets/catalog.json"
            return f'bash -c "cat /tmp/{data_file} | {command_base}"'

        def process_src_image(image):
            try:
                self.pull_docker_image(image)
                volumes = self._prepare_src_volumes(output_file_path)
                self.run_image_check(image, volumes)
                full_command = construct_src_command()
                container_name = f"{image.replace('/', '-')}_{uuid.uuid4()}"
                
                # Log that the source container process has started
                self.logger.info(f"Starting data source sync process for {image}...")
        
                self._run_container_with_entrypoint(
                    image, full_command, volumes, container_name
                )
                
                 # Log that the source container process has completed
                self.logger.info(f"Completed data source sync for {image}.")
        
            except Exception as e:
                self.logger.error(
                    f"Error processing source image {image}: {str(e)}"
                )
                return False
            return True

        def process_dst_image(image):
            try:
                self.pull_docker_image(image)
                volumes = self._prepare_dst_volumes(output_file_path)
                self.run_image_check(image, volumes)
                full_command = construct_dst_command()
                container_name = f"{image.replace('/', '-')}_{uuid.uuid4()}"
                
                 # Log that the destination container process has started
                self.logger.info(f"Starting load to {image} data destination...")
        
                self._run_container_with_entrypoint(
                    image, full_command, volumes, container_name
                )
                
                # Log that the destination container process has completed
                self.logger.info(f"Completed load to {image} data destination.")
       
       
            except Exception as e:
                self.logger.error(
                    f"Error processing destination image {image}: {str(e)}"
                )
                return False
            return True

        # Process Source Image
        if not process_src_image(src_airbyte_image):
            return False

        # Process Destination Image
        if dst_airbyte_image and not process_dst_image(dst_airbyte_image):
            return False

        return True

    def final_cleanup(self) -> None:
        """Cleanup all active containers."""
        for container_name in self.active_containers[:]:
            if self.cleanup_container(container_name):
                self.active_containers.remove(container_name)
        self.logger.info("All cleanup processes are finished.")


class ContainerExecutionError(Exception):
    """Exception raised when there's an error in executing the Docker
    container."""

class DockerImageNotFoundError(Exception):
    """Custom exception indicating a missing Docker image."""

    def __init__(self, message="Docker image not found"):
        super().__init__(message)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""

    def __init__(self, message="Configuration error"):
        super().__init__(message)


@dataclass
class Config:
    """Configuration for Airbyte source and destination."""

    src_config_loc: str = ""  # Source configuration location
    dst_config_loc: str = ""  # Destination configuration location
    catalog_loc: str = ""  # Catalog location


@dataclass
class ImageInfo:
    """Information about Airbyte image source and destination."""

    src_image: str = ""  # Source Airbyte image
    dst_image: str = ""  # Destination Airbyte image


def parse_airbyte_arguments(default_config=None) -> argparse.Namespace:
    """Parse command-line arguments for the Airbyte Docker Runner."""
    default_config = default_config or {}

    parser = argparse.ArgumentParser(description="Airbyte Docker Runner")

    # Source arguments
    parser.add_argument(
        "-i",
        "--airbyte-src-image",
        default=default_config.get("airbyte-src-image"),
        help="Airbyte source connector Docker image.",
    )
    parser.add_argument(
        "-s",
        "--src-config-loc",
        default=default_config.get("src-config-loc"),
        help="Source connector configuration file path.",
    )

    # Destination arguments
    parser.add_argument(
        "-w",
        "--airbyte-dst-image",
        default=default_config.get("airbyte-dst-image"),
        help="Airbyte destination connector Docker image.",
    )
    parser.add_argument(
        "-d",
        "--dst-config-loc",
        default=default_config.get("dst-config-loc"),
        help="Destination connector configuration file path.",
    )

    # Miscellaneous arguments
    parser.add_argument(
        "-c",
        "--catalog-loc",
        default=default_config.get("catalog-loc"),
        help="Catalog file path.",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        default=default_config.get("output-path"),
        help="Output directory path.",
    )
    parser.add_argument(
        "-t",
        "--state-file-path",
        default=default_config.get("state-file-path"),
        help="State file path. Uses default catalog state if omitted.",
    )
    parser.add_argument(
        "-r", "--runtime-configs", help="External configuration file path."
    )
    parser.add_argument(
        "-j",
        "--job",
        default=default_config.get("job"),
        type=str,
        help="Unique Job ID. If omitted, one is generated.",
    )

    args = parser.parse_args()

    # Compute the MD5 hash of the source configuration file
    args.source_config_hash = src_config_md5(args.src_config_loc)

    # Generate a job ID if not provided
    args.job = args.job or f"jobid-{src_runtime}"
    
    # Set the log file path
    fh = logging.FileHandler(f"{args.output_path}/out.log", "w")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    formatter.datefmt = "%Y-%m-%d %H:%M:%S"
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return args


def handle_docker(args):
    """Set up and return the Docker handler based on provided arguments."""
    logging.info("\U0001F680 Initiating your Airbridge data workflow...")

    state_message = (
        f"A state file was passed: {args.state_file_path}"
        if args.state_file_path
        else "No state file was passed for your source, using catalog defaults..."
    )
    logging.info(state_message)

    try:
        handler = AirbyteDockerHandler(
            configuration=vars(args),
            output_path=args.output_path,
            src_image=args.airbyte_src_image,
            dst_image=args.airbyte_dst_image,
            src_runtime=src_runtime,
        )
        handler.load_config_from_args(args)
        return handler
    except Exception as error:
        logging.error(f"Error encountered of type {type(error)}: {error}")
        return None


def handle_state(args):
    """Execute the state handler based on provided arguments."""
    try:
        executor = StateHandler(
            output_path=args.output_path,
            airbyte_src_image=args.airbyte_src_image,
            source_config_hash=args.source_config_hash,
            job_id=getattr(args, "job", None),
        )
        executor.execute()
    except Exception as error:
        logging.error(
            f"Error executing state script of type {type(error)}: {error}"
        )
        raise RuntimeError("Failed executing state script.") from error


def main():
    """Main execution function."""
    with LockManager():
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "-r",
                "--runtime-configs",
                default=None,
                help="Path to an external configuration file for additional settings.",
            )
            temp_args = parser.parse_known_args()[0]

            config_manager = ConfigManager(
                config_file=getattr(temp_args, "runtime_configs", None)
            )
            args = parse_airbyte_arguments(default_config=config_manager.config)
            config_manager.update_from_args(args)

            handler = handle_docker(args)
            if handler:
                handler.execute()
                handle_state(args)
                handler.final_cleanup()
                logging.info(
                    "Your Airbridge data workflow has completed successfully! \u2728 \U0001F370 \u2728"
                )
            else:
                logging.warning("Docker handler was not initialized.")
        except Exception as error:
            logging.error(
                f"Unexpected error of type {type(error)}: {error}",
                exc_info=True,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
