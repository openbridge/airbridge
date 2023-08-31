

# Data Destination: Amazon S3

## Background
When using the S3 destination Airbyte connector (`airbyte/destination-s3`, your data will store data to Amazon S3. Why select S3 as a default? S3 is a data lake "landing zone" for raw connector output. The data lake landing zone is the initial area where raw data is stored for later ingestion or processing. Data is defaulted to a gzipped CSV file format. 

The pattern is a typical data lake landing zone approach defined by different cloud platforms and service providers. For example, both AWS and Databricks include the concept of a landing zone within a data lake. AWS calls it the Raw Data Layer, while Databricks often frames this as the Bronze Layer.

Data output to S3 ensures that Airbyte outputs sent to the data lake's landing zone are optimized for scalability, reliability, cost-effectiveness, and ease of data processing.

## How Data Is Organized In Your S3 Bucket
Adhering to best practices for object key or folder naming and partitioning is crucial for efficient data management, access, and query performance. 

The pattern we defined below represents a structured way to organize and name data objects, within an S3 bucket or similar storage system. 

Let's break down each component of this pattern:

### Path

1. **`airbyte-stripe/`**:
    - This is the top-level prefix or "folder" that suggests the data is related to the "stripe" source ingested by Airbyte. 
    - It clearly indicates the data source, which can be useful for an organization, especially if you have multiple data sources.

2. **`${STREAM_NAME}/`**:
    - Represents the name of the data stream. In the context of Airbyte, a stream typically corresponds to a table or entity in the source system. 
    - Partitioning by stream name makes locating and managing all data related to a specific table or entity easy.

3. **`dt=${YEAR}${MONTH}${DAY}/`**:
    - This is a date-based partitioning scheme. 
    - The `dt=` prefix suggests it's a date stamp, followed by the exact date constructed from the YEAR, MONTH, and DAY placeholders.
    - Data lakes commonly use date-based partitioning to organize and query time-series data efficiently.

### Filename

4. **`${SOURCE_NAMESPACE}_`**:
    - Represents the namespace of the source, which could be a specific database, schema, or another form of data categorization within the source system.
    - Including the namespace in the object name can help differentiate data from different namespaces but with the same stream name.

5. **`${STREAM_NAME}_`**:
    - Again, this represents the name of the data stream. Including it in the actual object name (as well as the path) provides redundancy and clarity, especially when viewing individual objects without their full path.

6. **`${EPOCH}_`**:
    - Represents a timestamp in the Unix epoch format, which counts seconds since the "epoch": 1970-01-01 00:00:00 UTC. 
    - This can precisely indicate when the data was ingested or processed.

7. **`${UUID}`**:
    - This is a universally unique identifier. Including a UUID ensures that each object name is unique, even if multiple objects are created for the same stream on the same day and at the same epoch second. 
    - The inclusion of a universally unique identifier (${UUID}) in the object naming convention ensures that every file name is distinct and one-of-a-kind. UUIDs are designed to be unique across time and space, so even if two objects are generated for the same stream, from the same namespace, on the same day, and even at the same epoch second, their UUIDs will differentiate them. This uniqueness is paramount in a data ingestion system like Airbyte, where data from various sources might be ingested concurrently. By ensuring each file has a unique name, the system prevents potential filename collisions, overwrites, or data loss, thereby maintaining data integrity and consistency in the storage layer.

### Example
The pattern `airbyte-stripe/${STREAM_NAME}/dt=${YEAR}${MONTH}${DAY}/${SOURCE_NAMESPACE}_${STREAM_NAME}_${EPOCH}_${UUID}` is a structured naming convention for organizing data ingested by Airbyte from a "stripe" source. It uses a combination of source-specific prefixes, date-based partitioning, stream names, namespaces, timestamps, and UUIDs to create clear, unique, and informative object names, optimizing for organizational clarity and query efficiency.


## AWS S3 Setup Guide
This section provides the reference information for Amazon S3.

### Prerequisites

To set up AWS S3 as your Airbyte service's destination, you must ensure you have the following information.

### 1. AWS Account
- **Description**: You need an Amazon Web Service account before you begin. 

### 2. Access Key Id
- **Description**: This is a unique identifier for AWS users.
- **Steps**: [How to Generate an Access Key Id](https://aws.amazon.com/documentation/access-key-id-generation)
- **Recommendation**: We suggest creating a user specifically for Airbyte. Ensure this user has read and write permissions for objects in the S3 bucket.

### 3. Secret Access Key

- **Description**: This private key corresponds to the Access Key ID mentioned above.
- **Note**: Keep this key confidential, as it provides access to your AWS resources.

### 4. S3 Bucket Name

- **Description**: This is the name of the S3 bucket where your data will be stored.
- **Steps**: [How to Create an S3 Bucket](https://aws.amazon.com/documentation/create-s3-bucket)

### 5. S3 Bucket Path

- **Description**: This specifies the subdirectory within the named S3 bucket where the data will be synchronized.
- **Note**: Think of this as a folder within your bucket.

### 5. S3 Bucket Region

- **Description**: The geographical region where the S3 bucket is hosted.
- **Reference**: [List of All AWS Region Codes](https://aws.amazon.com/documentation/region-codes)

## AWS S3 Automated Configuration
Amazon CloudFormation is a service offered by AWS that allows users to define, deploy, and manage infrastructure resources using templated scripts. With the CloudFormation template formation script we provide, you can automate the entire S3 infrastructure stack.

To simplify the setup process, everything we detailed above for Steps 2-5 can be automated with our ready-to-go CloudFormation template. 

### Template Overview
 The template is designed to automate the complete setup of your AWS account resources needed for storing Airbyte connector outputs on Amazon S3. This includes ensuring your Airbyte service has the necessary permissions to access and manage the data.

- Auto creates an S3 bucket generated using the pattern `openbridge-{AccountId}-{Region}-{StackName}`.
- Creates a new IAM user named "`AirbyteUser.`"
- Attaches an IAM policy to the `AirbyteUser.`
- Grants the user permissions (`s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`) to access and manage the data in your bucket.
- Generates an access key for the AirbyteUser, which allows programmatic access to AWS resources.

*Note: The bucket's data will be retained even if the CloudFormation stack is deleted due to the `DeletionPolicy: Retain.`*

### Download Template
Download the [cf-s3destination.yaml](./cloudformation.cf-s3destination.yaml) template.

### Create and save your S3 config

Replace the placeholder values below from the outputs that were generated from your CloudFormation process:

- `s3_bucket_name`
- `access_key_id`
- `secret_access_key`


#### Settings
Here is the S3 config needed to store your outputs in S3. Use a descriptive name like `s3-destination.json`;

```JSON
{
    "s3_bucket_name": "XXXXXX",
    "s3_bucket_path": "ebs/ftpd",
    "s3_path_format": "airbyte-stripe/${STREAM_NAME}/dt=${YEAR}${MONTH}${DAY}/${SOURCE_NAMESPACE}_${STREAM_NAME}_${EPOCH}_${UUID}",
    "s3_bucket_region": "us-east-1",
    "access_key_id": "XXXXX",
    "secret_access_key": "XXXXX",
    "format": {
        "format_type": "CSV",
        "flattening": "Root level flattening",
        "compression": { 
            "compression_type": "GZIP" 
        }
    }
}
```