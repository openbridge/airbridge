# Airbridge: Lightweight Airbyte Data Flows

Airbridge uses base Airbyte Docker images, so you can concentrate on simple, well-bounded data extraction and delivery while using the minimum resources to get the job done. Pick your Airbyte source and your Airbyte destination; Airbridge handles the rest.

### Overview

🐳 **Docker-Driven**: Utilizes prebuilt source and destination Docker images via Docker Hub.

🐍 **Python-Powered**: Built on standards-based Python, Airbridge ensures a clean, quick, and modular data flow, allowing for easy integration and modification.

🔗 **Airbyte Sources and Destinations**: Orchestrating the resources needed to bridge Sources and Destinations into a data workflow.

🔄 **Automated State Management**: Includes simple, but effective, automated state tracking for each run.

🔓 **Open-Source**: No special license, everything Airbridge is MIT.

📦 **No Bloat**: No proprietary packages. No unnecessary wrappers.

📜 **License Simplicity**: No intricate licensing models to decipher. Airbridge is MIT licensed.


## Prerequisites
The Airbridge project requires Docker and Python:

1. **Docker**: The project uses Airbyte Docker images, which containerize source and destination connectors, ensuring a consistent and isolated environment for them. See [Docker for Linux](https://docs.docker.com/engine/install/),[Docker Desktop for Windows](https://docs.docker.com/docker-for-windows/install/),[Docker Desktop for Mac](https://docs.docker.com/docker-for-mac/install/)
2. **Python**: The project is written in Python and requires various Python packages to function correctly. Download and install the required version from [Python's official website](https://www.python.org/downloads/).


## Quick Start

You have Python and Docker installed. Docker is running and you are ready to go!

The fastest way to get started is via Poetry. 

To install Poetry, you can use Python (or Python3);

```
curl -sSL https://install.python-poetry.org | python -
curl -sSL https://install.python-poetry.org | python3 -
```

Once installed, go into the Airbridge project folder, then run the install:
```
poetry install
```
Make sure you are in the `src/airbridge` directory, then you can
run Airbridge using a simple Python command like this;

```bash
poetry run main  -i airbyte/source-stripe -w airbyte/destination-s3 -s /airbridge/env/stripe-source-config.json -d /airbridge/env/s3-destination-config.json -c /airbridge/env/stripe-catalog.json  -o /airbridge/tmp/mydataoutput/
```
The above command is an example. It shows a connection to Stripe, collecting all the data defined in the catalog, then send the data to Amazon S3. Thats it.

After running these two commands, in your local output path you will see;

```tree
- airbridge
  - tmp
    - mydataoutput
      - airbyte
        - source-stripe
          - 1629876543
            - data.json
            - state.json
```
How this data is represented in your destination will vary according to configs you supplied. 

For Airbridge to work, it needs Airbyte defined configs. Configs define credentials and catalogs.

## Overview of Configs
In our example `run` command we passed a collection of arguments. 

First, we defined the Airbyte docker source image name. We used `-i airbyte/source-stripe` in our command because we want to use Stripe as a source. 
 
 Next, we set the destination. This is where you want `airbyte/source-stripe` data to land. In our command, we used `-w airbyte/destination-s3` because we want data from Stripe to be sent to our Amazon S3 data lake. 
 
 We passed `-c /env/stripe-catalog.json` because this reflects the catalog of the `airbyte/source-stripe` source. The catalog defines the schemas and other elements of what is supplied via `airbyte/source-stripe`.
 
 Lastly, we set a tmp location to store the data from the source prior to sending it to your destination. We passed `-o /tmp/467d8d8c57ea4eaea7670d2b9aec7ecf` to store the output of `airbyte/source-stripe` prior to posting to `airbyte/destination-s3`.

You could quickly switch things up, using `airbyte/source-klaviyo` and keep your destination of `airbyte/destination-s3`. 

All you need to do is swap Klaviyo source(`klaviyo-source-config.json`) and catalog(`klaviyo-catalog.json`), but leave unchanged S3 (`s3-destination-config.json`) and the local source output(`/airbridge/tmp/mydataoutput/`).

### Passing Your Config Arguments
 The following arguments can be provided to Airbridge:

- **-i**:  The Airbyte source image from Docker Hub (required). Select a pre-built source image from Docker hub [Airbyte source connector]( https://hub.docker.com/u/airbyte).
- **-w**: The Airbyte destination image from Docker Hub (required). Select a pre-built source image from Docker hub [Airbyte destination connector]( https://hub.docker.com/u/airbyte). This is where you want your data landed.
- **-s**: The configuration (`<source>-config.json`) for the source. 
- **-d**: The configuration (`<destination>-config.json`) for the destination.
- **-c**: The catalog configuration for both source and destination.
- **-o**: The desired path for local data output. This is where the raw data from the connector is temporarily stored.
- **-j**: Job ID associated with the process.
- **-t**: Path to the state file. If provided, the application will use the state file as an input to your run The state file.
- **-r**: Path to the external configuration file.

Rather than pass arguments, you can use a config file via `-r` like this `poetry run main -r ./config.json`. 

Here is an example config;
```json
{
    "airbyte-src-image": "airbyte/source-stripe",
    "airbyte-dst-image": "airbyte/destination-s3",
    "src-config-loc": "/path/to/airbridge/env/stripe-config.json",
    "dst-config-loc": "/path/to/airbridge/env/amazons3-config.json",
    "catalog-loc": "/path/to/airbridge/env/catalog.json",
    "output-path": "/path/to/airbridge/tmp/mydata",
    "job": "1234RDS34"
}
```


## Defining Your Configs

The principle effort running Airbridge will be setting up required Airbyte config files. As a result, the following documentation largely focuses on getting Airbyte configs setup correctly for your source and destinations.

### Deep Dive Into Configuration Files

As we have shown in our example, there are three configs that are needed to run the Airbyte service:
 1. **Source Credentials**: This relfects your authorization to the source. The content of this is defined by to Airbyte connector `spec.json`. Typically there will be a `sample_files/sample_config.json` in a connector directory to use as a reference config file.
 2. **Source Data Catalog**: The catalog, often named something like `configured_catalog.json`, reflects the datasets and schemas defined by the connector. 
 1. **Destination Credentials**: Like the Source connector, this reflects your authorization to the destination.

Each of these configs are defined by the Airbyte source or destination. As such, you need to follow the specifications they set exactly as they define them. This includes both required or optional elements. To help with that process, we have created a config generation utility script, `config.py`.

### Auto Generate Airbyte Config Templates With `config.py`
Not all Airbyte connectors and destinations contain reference config files. This can make it challenging to determine what should be included in source (or destination) credential file.

To simplify the process of creating the source and destination credentials, you can run `config.py`. This script will generate a configuration file based on a the specific source or destination specification (`spec.json` or `spec.yaml`) file. It can also create a local copy of the `catalog.json`. 

#### Locating The `spec.json` or `spec.yaml` files
To find the `spec.json` or `spec.yaml`, you will need to navigate to the respective sources on [Github](
 https://github.com/airbytehq/airbyte/tree/master/airbyte-integrations/connectors). For example, you were interested in Stripe, go to `connectors/source-stripe/`. In that folder, you would find the `spec.yaml` in `connectors/source-stripe/source_stripe/spec.yaml`. 
 
 For LinkedIn, you go to `connectors/source-linkedin-ads` and the navigate to `connectors/source-linkedin-ads/source_linkedin_ads/spec.json`

#### Locating The `catalog.json` files
To find the `catalog.json`, you will need to navigate to the respective sources on [Github](
 https://github.com/airbytehq/airbyte/tree/master/airbyte-integrations/connectors). For example, you were interested in Chargebee, go to `source-chargebee/integration_tests/`. In that folder, you would find the `configured_catalog.json`. 


*NOTE: Always make sure you are passing the `RAW` output of the `yaml` or `json` file. For example, the GitHib link to the raw file will look like `https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-linkedin-ads/source_linkedin_ads/spec.json`.*


#### Running The Config Generation Script
The script accepts command-line arguments to specify the input spec file URL and the output path for the generated configuration file.

To run `config.py`, make sure to run `pip install requests jsonschema` if you do not have them installed. *Note: If you're using a Python environment where pip refers to Python 2, you might want to use pip3 instead of pip.*

The script takes an input and generates the config as an output via the following arguments;

- The `-i` or `--input` argument specifies the URL of the spec file (either YAML or JSON format).
- The `-o` or `--output` argument specifies the path where the generated configuration file should be saved.
- The `-c` or `--catalog` argument specifies the URL of the catalog file (either YAML or JSON format).

Example usage:

  ```python
  python3 config.py -i https://example.com/spec.yaml -o ./config/my-config.json
  ```

This example uses the `source_klaviyo/spec.json` from Github:
  ```python
  python3 config.py -i https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-klaviyo/source_klaviyo/spec.json -o ./my-klaviyo-config.json
  ```

In this example, you do not specify the name when passing `-o`. You simply pass the folder:

```python
python3 config.py -i https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/destination-s3/src/main/resources/spec.json -o ./config
```
If a filename is not passed, the script will auto generate the file name based on the value of `title` in `spec.json`. In this example, the config name would be `s3-destination-spec-config.json`. 

This will connect, collect, and then store the `configured_catalog.json` locally to `./config/catalog/source—chargebee-catalog.json`

```python
poetry run ./config.py -c https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-chargebee/integration_tests/configured_catalog.json -o ./config/catalog/source—chargebee-catalog.json

```

#### Example Configs
The generated configuration file contains placeholder values that can be replaced with actual values before use. The following is a `config.json` generated from the LinkedIn Ads `spec.json`. Note template config highlights required and optional fields as defined in the spec. You will need to supply these according to your specific use case.

```json
{
    "credentials": "optional_value",
    "client_id": "required_value",
    "client_secret": "required_value",
    "refresh_token": "required_value",
    "access_token": "required_value",
    "start_date": "required_value",
    "account_ids": "optional_value",
    "ad_analytics_reports": "optional_value"
}
```
The config below was generated from the S3 destination `destination-s3/src/main/resources/spec.json`. Note that is a little more involved than the LinkedIn config. This highlights some of the variations between different resources.

```json
{
    "access_key_id": "optional_value",
    "secret_access_key": "optional_value",
    "s3_bucket_name": "required_value",
    "s3_bucket_path": "required_value",
    "s3_bucket_region": "required_value",
    "format": {
        "format_type": "optional_value",
        "compression_codec": "optional_value",
        "flattening": "optional_value",
        "compression": {
            "compression_type": "optional_value"
        },
        "block_size_mb": "optional_value",
        "max_padding_size_mb": "optional_value",
        "page_size_kb": "optional_value",
        "dictionary_page_size_kb": "optional_value",
        "dictionary_encoding": "optional_value"
    },
    "s3_endpoint": "optional_value",
    "s3_path_format": "optional_value",
    "file_name_pattern": "optional_value"
}
```

Here is an example of an S3 `config.json` that removes the optional placeholders that are not needed;

```json
{
    "access_key_id": "1234565TYD45YU111X",
    "secret_access_key": "DSERFKGKFDUR459-123SAXVFKD",
    "s3_bucket_name": "my-unique-bucket-name",
    "s3_bucket_path": "airbyte/raw",
    "s3_bucket_region": "us-east-1",
    "format": {
        "format_type": "CSV",
        "flattening": "Root level flattening",
        "compression": {
            "compression_type": "GZIP"
        }
    },
    "s3_path_format": "airbyte-stripe/${STREAM_NAME}/dt=${YEAR}${MONTH}${DAY}/${SOURCE_NAMESPACE}_${STREAM_NAME}_${EPOCH}_${UUID}"
}
```

## Tracking Your Runs
In the realm of data processing, especially when dealing with data synchronization, logging, or orchestration tasks, it's crucial to have a way to uniquely identify each execution or "job". This is especially true given the use of a state file informs Airbyte where you want to start or where you left off.

This is where the concept of a "Job ID" comes into play.

#### What is a Job ID?
A Job ID is a unique identifier assigned to a specific execution or "run" of a process or script. In the context of the Airbyte Docker Runner, passing a Job ID via **-j** serves as a unique tag that can differentiate one run of the script from another. This becomes especially important when multiple instances of the script might be running concurrently, or when you need to trace back the results, logs, or errors of a specific execution.

#### Passing a Job ID
In the context of the Airbyte Docker Runner, the Job ID can be provided via the -j or --job argument, allowing users or systems to determine the method of uniqueness that best fits their needs. If not provided, the script or system could default to generating one using a method like the above.

#### What should the Job ID be?
While the method for generating a Job ID can vary based on the system or requirements, common practices include:

- **Timestamps**: Using a precise timestamp (down to milliseconds or microseconds) ensures uniqueness, as no two moments in time are the same.
- **UUIDs**: Universally Unique Identifiers are designed to be unique across time and space and can be generated without requiring a centralized authority.
- **Sequential IDs**: In systems with a central authority or database, IDs can be generated sequentially.

Ultimately, what is used should map to setting a meaningful key that is relevant to your use case.


## Tracking State
The `state.json` file plays a crucial role in incremental data extraction processes. In the context of Airbyte or similar data integration tools, the state file keeps track of the last data extraction point. This ensures that in subsequent runs, the script only processes records that have been updated or created after the last extraction, rather than reprocessing the entire dataset.

The contents of the `state.json` file are derived from the `data.json` output, which is generated by the source worker during the data extraction process. Essentially, the `data.json` file defines the current state of data at the source during a particular run. As a result, `data.json` acts as the blueprint for the `state.json` file, ensuring the state always accurately reflects the most recent extraction point.

### State Structure:
The file typically contains key-value pairs where the key represents a particular stream or table and the value represents the point up to which data has been extracted. For example:

```json
{
    "users": {
        "last_updated": "2023-08-24T10:37:49"
    },
    "orders": {
        "last_order_id": 31245
    }
}
```

In this example, the state.json file indicates that the users table was last extracted up to records updated at 2023-08-24T10:37:49, and the orders table was last extracted up to the order with ID 31245.

### Tracking State
The manifest file serves as a reference point for understanding the specifics of each job run. By inspecting the manifest, users can glean insights about the source and destination images, the current state of data extraction, and other vital metadata about the job. This can be particularly useful for optimizing your workflows, debugging or when trying to understand the flow and outcome of specific job runs.

A manifest will contain the following data;

- **Key**: A unique hash of the source config.
- **Job**: Represents the unique identifier for a specific run of the script. In the provided example, if you pass `-j boo123`, the manifest will reflect the path you the state file of your run. 
- **Source**: Name of the source, e.g., airbyte-source-stripe.
- **Path To Data File**: Full path to the data file associated with the job.
- **Path To State File**: The path to the `state.json` file, which captures the current state of data extraction for that particular run. For exmaple, you may want to use the most recent state file as an input to your next run `-t /path/to/state.json`. This allows you to optimize your workflows.
- **Run Timestamp**: Numeric value representing a timestamp emitted by Airbyte source.
- **Modified At**: Numeric value representing the time the entry was modified (or created).

The manifest JSOn will look like this;

```json
{
  "key": [
    {
      "jobid": "<Job Identifier>",
      "source": "<Source Name>",
      "data_file": "<Path to Data File>",
      "state_file_path": "<Path to State File>",
      "timestamp": <Timestamp Value>,
      "modified_at": <Modified Timestamp Value>
    }
  ]
}
```

Here is an example of the contents of a manifest file:

```json
{
  "7887ff97bdcc4cb8360cd0128705ea9b": [
    {
      "jobid": "RRRR1345",
      "source": "airbyte-source-stripe",
      "data_file": "/tmp/mydata/airbyte-source-stripe/1693311748/data_1693311747.json",
      "state_file_path": "/tmp/mydata/airbyte-source-stripe/1693311748/state.json",
      "timestamp": 1693311748,
      "modified_at": 1693311795
    },
    {
      "jobid": "RRRR1346",
      "source": "airbyte-source-stripe",
      "data_file": "/tmp/mydata/airbyte-source-stripe/1693313177/data_1693313176.json",
      "state_file_path": "/tmp/mydata/airbyte-source-stripe/1693313177/state.json",
      "timestamp": 1693313177,
      "modified_at": 1693313222
    }
  ]
}
```


## Install Python
Here's a step-by-step guide on how to check if Python is installed and its version, along with instructions for installing Python on macOS, Windows 10+, and Ubuntu Linux:

### Checking Python Installation and Version

1. **Check if Python is Installed:**
   Open a terminal or command prompt and enter the following command:
   
   ```bash
   python --version
   ```

   If Python is installed, the version number will be displayed. If it's not installed, you'll see an error message.

2. **Check Python Version:**
   To check the exact version of Python installed, you can run:
   
   ```bash
   python -V
   ```

### Installing Python on macOS

1. **Check Installed Version (if any):**
   Open the terminal and run the following command to check if Python is already installed:

   ```bash
   python --version
   ```

2. **Install Homebrew (if not installed):**
   If Homebrew is not installed, you can install it using the following command:

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install Python using Homebrew:**
   After installing Homebrew, you can install Python with the following command:

   ```bash
   brew install python
   ```

### Installing Python on Windows 10+

1. **Download Python Installer:**
   Visit the official Python website (https://www.python.org/downloads/) and download the latest version of Python for Windows.

2. **Run Installer:**
   Double-click the downloaded installer (.exe) file and follow the installation wizard. Make sure to check the option "Add Python to PATH" during installation.

3. **Verify Installation:**
   Open Command Prompt (cmd) and run the following command to verify the installation:

   ```bash
   python --version
   ```

### Installing Python on Ubuntu Linux

1. **Check Installed Version (if any):**
   Open the terminal and run the following command to check if Python is already installed:

   ```bash
   python3 --version
   ```

2. **Update Package List:**
   Run the following command to update the package list:

   ```bash
   sudo apt update
   ```

3. **Install Python:**
   Install Python 3 using the following command:

   ```bash
   sudo apt install python3
   ```

### Additional Notes

- On Linux, you might use `python3` and `python3.x` to specify the Python version, as `python` often refers to Python 2.
- On Windows, you can use "Command Prompt" or "PowerShell" to run the commands.
- Python's official website provides detailed installation guides for various platforms: https://www.python.org/downloads/installing/

Make sure to adjust the commands as needed based on your system configuration and requirements.

## Set Up the Python Environment with Poetry

Poetry is a dependency management and packaging tool that simplifies working with Python. If you want to use Poetry, see the steps below:


- **Install Poetry**: You can install via `curl -sSL https://install.python-poetry.org | python3`.

- **Install Project Dependencies**: To get your environment ready, run `poetry install`. This command will install both the runtime and development dependencies for the project in an isolated virtual environment managed by Poetry.

## Frequenlty Asked Questions

#### **I'm getting permissions issues when running `run.py` or `config.py`**
You may need to setting permissions `chmod +x run.py config.py` if you get permission denied.

## Reference Source Documentation Pages

The following is a collection of data source documentation. This is not meant to be comprehesive list, merely a waypoint to help get people headed in the right direction.

| Connector Name | Documentation Page |
| --- | --- |
| Postgres | [Postgres](https://docs.airbyte.com/integrations/sources/postgres) |
| ActiveCampaign | [ActiveCampaign](https://docs.airbyte.com/integrations/sources/activecampaign) |
| Adjust | [Adjust](https://docs.airbyte.com/integrations/sources/adjust) |
| Aha API | [Aha API](https://docs.airbyte.com/integrations/sources/aha) |
| Aircall | [Aircall](https://docs.airbyte.com/integrations/sources/aircall) |
| Airtable | [Airtable](https://docs.airbyte.com/integrations/sources/airtable) |
| AlloyDB for PostgreSQL | [AlloyDB for PostgreSQL](https://docs.airbyte.com/integrations/sources/alloydb) |
| Alpha Vantage | [Alpha Vantage](https://docs.airbyte.com/integrations/sources/alpha-vantage) |
| Amazon Ads | [Amazon Ads](https://docs.airbyte.com/integrations/sources/amazon-ads) |
| Amazon Seller Partner | [Amazon Seller Partner](https://docs.airbyte.com/integrations/sources/amazon-seller-partner) |
| Amazon SQS | [Amazon SQS](https://docs.airbyte.com/integrations/sources/amazon-sqs) |
| Amplitude | [Amplitude](https://docs.airbyte.com/integrations/sources/amplitude) |
| Apify Dataset | [Apify Dataset](https://docs.airbyte.com/integrations/sources/apify-dataset) |
| Appfollow | [Appfollow](https://docs.airbyte.com/integrations/sources/appfollow) |
| Apple Search Ads | [Apple Search Ads](https://docs.airbyte.com/integrations/sources/apple-search-ads) |
| AppsFlyer | [AppsFlyer](https://docs.airbyte.com/integrations/sources/appsflyer) |
| Appstore | [Appstore](https://docs.airbyte.com/integrations/sources/appstore-singer) |
| Asana | [Asana](https://docs.airbyte.com/integrations/sources/asana) |
| Ashby | [Ashby](https://docs.airbyte.com/integrations/sources/ashby) |
| Auth0 | [Auth0](https://docs.airbyte.com/integrations/sources/auth0) |
| AWS CloudTrail | [AWS CloudTrail](https://docs.airbyte.com/integrations/sources/aws-cloudtrail) |
| Azure Blob Storage | [Azure Blob Storage](https://docs.airbyte.com/integrations/sources/azure-blob-storage) |
| Azure Table Storage | [Azure Table Storage](https://docs.airbyte.com/integrations/sources/azure-table) |
| Babelforce | [Babelforce](https://docs.airbyte.com/integrations/sources/babelforce) |
| Bamboo HR | [Bamboo HR](https://docs.airbyte.com/integrations/sources/bamboo-hr) |
| Baton | [Baton](https://docs.airbyte.com/integrations/sources/baton) |
| BigCommerce | [BigCommerce](https://docs.airbyte.com/integrations/sources/bigcommerce) |
| BigQuery | [BigQuery](https://docs.airbyte.com/integrations/sources/bigquery) |
| Bing Ads | [Bing Ads](https://docs.airbyte.com/integrations/sources/bing-ads) |
| Braintree | [Braintree](https://docs.airbyte.com/integrations/sources/braintree) |
| Braze | [Braze](https://docs.airbyte.com/integrations/sources/braze) |
| Breezometer | [Breezometer](https://docs.airbyte.com/integrations/sources/breezometer) |
| CallRail | [CallRail](https://docs.airbyte.com/integrations/sources/callrail) |
| Captain Data | [Captain Data](https://docs.airbyte.com/integrations/sources/captain-data) |
| Cart.com | [Cart.com](https://docs.airbyte.com/integrations/sources/cart) |
| Chargebee | [Chargebee](https://docs.airbyte.com/integrations/sources/chargebee) |
| Chargify | [Chargify](https://docs.airbyte.com/integrations/sources/chargify) |
| Chartmogul | [Chartmogul](https://docs.airbyte.com/integrations/sources/chartmogul) |
| ClickHouse | [ClickHouse](https://docs.airbyte.com/integrations/sources/clickhouse) |
| ClickUp API | [ClickUp API](https://docs.airbyte.com/integrations/sources/clickup-api) |
| Clockify | [Clockify](https://docs.airbyte.com/integrations/sources/clockify) |
| Close.com | [Close.com](https://docs.airbyte.com/integrations/sources/close-com) |
| CockroachDB | [CockroachDB](https://docs.airbyte.com/integrations/sources/cockroachdb) |
| Coda | [Coda](https://docs.airbyte.com/integrations/sources/coda) |
| CoinAPI | [CoinAPI](https://docs.airbyte.com/integrations/sources/coin-api) |
| CoinGecko Coins | [CoinGecko Coins](https://docs.airbyte.com/integrations/sources/coingecko-coins) |
| Coinmarketcap API | [Coinmarketcap API](https://docs.airbyte.com/integrations/sources/coinmarketcap) |
| Commcare | [Commcare](https://docs.airbyte.com/integrations/sources/commcare) |
| Commercetools | [Commercetools](https://docs.airbyte.com/integrations/sources/commercetools) |
| Configcat API | [Configcat API](https://docs.airbyte.com/integrations/sources/configcat) |
| Confluence | [Confluence](https://docs.airbyte.com/integrations/sources/confluence) |
| ConvertKit | [ConvertKit](https://docs.airbyte.com/integrations/sources/convertkit) |
| Convex | [Convex](https://docs.airbyte.com/integrations/sources/convex) |
| Copper | [Copper](https://docs.airbyte.com/integrations/sources/copper) |
| Courier | [Courier](https://docs.airbyte.com/integrations/sources/courier) |
| Customer.io | [Customer.io](https://docs.airbyte.com/integrations/sources/customer-io) |
| Datadog | [Datadog](https://docs.airbyte.com/integrations/sources/datadog) |
| DataScope | [DataScope](https://docs.airbyte.com/integrations/sources/datascope) |
| Db2 | [Db2](https://docs.airbyte.com/integrations/sources/db2) |
| Delighted | [Delighted](https://docs.airbyte.com/integrations/sources/delighted) |
| Dixa | [Dixa](https://docs.airbyte.com/integrations/sources/dixa) |
| Dockerhub | [Dockerhub](https://docs.airbyte.com/integrations/sources/dockerhub) |
| Dremio | [Dremio](https://docs.airbyte.com/integrations/sources/dremio) |
| Drift | [Drift](https://docs.airbyte.com/integrations/sources/drift) |
| Drupal | [Drupal](https://docs.airbyte.com/integrations/sources/drupal) |
| Display & Video 360 | [Display & Video 360](https://docs.airbyte.com/integrations/sources/dv-360) |
| Dynamodb | [Dynamodb](https://docs.airbyte.com/integrations/sources/dynamodb) |
| End-to-End Testing Source for Cloud | [End-to-End Testing Source for Cloud](https://docs.airbyte.com/integrations/sources/e2e-test-cloud) |
| End-to-End Testing Source | [End-to-End Testing Source](https://docs.airbyte.com/integrations/sources/e2e-test) |
| Elasticsearch | [Elasticsearch](https://docs.airbyte.com/integrations/sources/elasticsearch) |
| EmailOctopus | [EmailOctopus](https://docs.airbyte.com/integrations/sources/emailoctopus) |
| Everhour | [Everhour](https://docs.airbyte.com/integrations/sources/everhour) |
| Exchange Rates API | [Exchange Rates API](https://docs.airbyte.com/integrations/sources/exchange-rates) |
| Facebook Marketing | [Facebook Marketing](https://docs.airbyte.com/integrations/sources/facebook-marketing) |
| Facebook Pages | [Facebook Pages](https://docs.airbyte.com/integrations/sources/facebook-pages) |
| Faker | [Faker](https://docs.airbyte.com/integrations/sources/faker) |
| Fastbill | [Fastbill](https://docs.airbyte.com/integrations/sources/fastbill) |
| Fauna | [Fauna](https://docs.airbyte.com/integrations/sources/fauna) |
| Files (CSV, JSON, Excel, Feather, Parquet) | [Files (CSV, JSON, Excel, Feather, Parquet)](https://docs.airbyte.com/integrations/sources/file) |
| Firebase Realtime Database | [Firebase Realtime Database](https://docs.airbyte.com/integrations/sources/firebase-realtime-database) |
| Firebolt | [Firebolt](https://docs.airbyte.com/integrations/sources/firebolt) |
| Flexport | [Flexport](https://docs.airbyte.com/integrations/sources/flexport) |
| Freshcaller | [Freshcaller](https://docs.airbyte.com/integrations/sources/freshcaller) |
| Freshdesk | [Freshdesk](https://docs.airbyte.com/integrations/sources/freshdesk) |
| Freshsales | [Freshsales](https://docs.airbyte.com/integrations/sources/freshsales) |
| Freshservice | [Freshservice](https://docs.airbyte.com/integrations/sources/freshservice) |
| FullStory | [FullStory](https://docs.airbyte.com/integrations/sources/fullstory) |
| Gainsight-API | [Gainsight-API](https://docs.airbyte.com/integrations/sources/gainsight-px) |
| GCS | [GCS](https://docs.airbyte.com/integrations/sources/gcs) |
| Genesys | [Genesys](https://docs.airbyte.com/integrations/sources/genesys) |
| getLago API | [getLago API](https://docs.airbyte.com/integrations/sources/getlago) |
| GitHub | [GitHub](https://docs.airbyte.com/integrations/sources/github) |
| GitLab | [GitLab](https://docs.airbyte.com/integrations/sources/gitlab) |
| Glassfrog | [Glassfrog](https://docs.airbyte.com/integrations/sources/glassfrog) |
| GNews | [GNews](https://docs.airbyte.com/integrations/sources/gnews) |
| GoCardless | [GoCardless](https://docs.airbyte.com/integrations/sources/gocardless) |
| Gong | [Gong](https://docs.airbyte.com/integrations/sources/gong) |
| Google Ads | [Google Ads](https://docs.airbyte.com/integrations/sources/google-ads) |
| Google Analytics 4 (GA4) | [Google Analytics 4 (GA4)](https://docs.airbyte.com/integrations/sources/google-analytics-data-api) |
| Google Analytics (Universal Analytics) | [Google Analytics (Universal Analytics)](https://docs.airbyte.com/integrations/sources/google-analytics-v4) |
| Google Directory | [Google Directory](https://docs.airbyte.com/integrations/sources/google-directory) |
| Google PageSpeed Insights | [Google PageSpeed Insights](https://docs.airbyte.com/integrations/sources/google-pagespeed-insights) |
| Google Search Console | [Google Search Console](https://docs.airbyte.com/integrations/sources/google-search-console) |
| Google Sheets | [Google Sheets](https://docs.airbyte.com/integrations/sources/google-sheets) |
| Google-webfonts | [Google-webfonts](https://docs.airbyte.com/integrations/sources/google-webfonts) |
| Google Workspace Admin Reports | [Google Workspace Admin Reports](https://docs.airbyte.com/integrations/sources/google-workspace-admin-reports) |
| Greenhouse | [Greenhouse](https://docs.airbyte.com/integrations/sources/greenhouse) |
| Gridly | [Gridly](https://docs.airbyte.com/integrations/sources/gridly) |
| Gutendex | [Gutendex](https://docs.airbyte.com/integrations/sources/gutendex) |
| Harness | [Harness](https://docs.airbyte.com/integrations/sources/harness) |
| Harvest | [Harvest](https://docs.airbyte.com/integrations/sources/harvest) |
| HTTP Request | [HTTP Request](https://docs.airbyte.com/integrations/sources/http-request) |
| Hubplanner | [Hubplanner](https://docs.airbyte.com/integrations/sources/hubplanner) |
| HubSpot | [HubSpot](https://docs.airbyte.com/integrations/sources/hubspot) |
| Insightly | [Insightly](https://docs.airbyte.com/integrations/sources/insightly) |
| Instagram | [Instagram](https://docs.airbyte.com/integrations/sources/instagram) |
| Instatus | [Instatus](https://docs.airbyte.com/integrations/sources/instatus) |
| Intercom | [Intercom](https://docs.airbyte.com/integrations/sources/intercom) |
| Intruder.io API | [Intruder.io API](https://docs.airbyte.com/integrations/sources/intruder) |
| Ip2whois API | [Ip2whois API](https://docs.airbyte.com/integrations/sources/ip2whois) |
| Iterable | [Iterable](https://docs.airbyte.com/integrations/sources/iterable) |
| Jenkins | [Jenkins](https://docs.airbyte.com/integrations/sources/jenkins) |
| Jira | [Jira](https://docs.airbyte.com/integrations/sources/jira) |
| K6 Cloud API | [K6 Cloud API](https://docs.airbyte.com/integrations/sources/k6-cloud) |
| Kafka | [Kafka](https://docs.airbyte.com/integrations/sources/kafka) |
| Klarna | [Klarna](https://docs.airbyte.com/integrations/sources/klarna) |
| Klaviyo | [Klaviyo](https://docs.airbyte.com/integrations/sources/klaviyo) |
| Kustomer | [Kustomer](https://docs.airbyte.com/integrations/sources/kustomer-singer) |
| Kyriba | [Kyriba](https://docs.airbyte.com/integrations/sources/kyriba) |
| Kyve Source | [Kyve Source](https://docs.airbyte.com/integrations/sources/kyve) |
| Launchdarkly API | [Launchdarkly API](https://docs.airbyte.com/integrations/sources/launchdarkly) |
| Lemlist | [Lemlist](https://docs.airbyte.com/integrations/sources/lemlist) |
| Lever Hiring | [Lever Hiring](https://docs.airbyte.com/integrations/sources/lever-hiring) |
| LinkedIn Ads | [LinkedIn Ads](https://docs.airbyte.com/integrations/sources/linkedin-ads) |
| LinkedIn Pages | [LinkedIn Pages](https://docs.airbyte.com/integrations/sources/linkedin-pages) |
| Linnworks | [Linnworks](https://docs.airbyte.com/integrations/sources/linnworks) |
| Lokalise | [Lokalise](https://docs.airbyte.com/integrations/sources/lokalise) |
| Looker | [Looker](https://docs.airbyte.com/integrations/sources/looker) |
| Magento | [Magento](https://docs.airbyte.com/integrations/sources/magento) |
| Mailchimp | [Mailchimp](https://docs.airbyte.com/integrations/sources/mailchimp) |
| MailerLite | [MailerLite](https://docs.airbyte.com/integrations/sources/mailerlite) |
| Mailersend | [Mailersend](https://docs.airbyte.com/integrations/sources/mailersend) |
| MailGun | [MailGun](https://docs.airbyte.com/integrations/sources/mailgun) |
| Mailjet - Mail API | [Mailjet - Mail API](https://docs.airbyte.com/integrations/sources/mailjet-mail) |
| Mailjet - SMS API | [Mailjet - SMS API](https://docs.airbyte.com/integrations/sources/mailjet-sms) |
| Marketo | [Marketo](https://docs.airbyte.com/integrations/sources/marketo) |
| Merge | [Merge](https://docs.airbyte.com/integrations/sources/merge) |
| Metabase | [Metabase](https://docs.airbyte.com/integrations/sources/metabase) |
| Microsoft Dataverse | [Microsoft Dataverse](https://docs.airbyte.com/integrations/sources/microsoft-dataverse) |
| Microsoft Dynamics AX | [Microsoft Dynamics AX](https://docs.airbyte.com/integrations/sources/microsoft-dynamics-ax) |
| Microsoft Dynamics Customer Engagement | [Microsoft Dynamics Customer Engagement](https://docs.airbyte.com/integrations/sources/microsoft-dynamics-customer-engagement) |
| Microsoft Dynamics GP | [Microsoft Dynamics GP](https://docs.airbyte.com/integrations/sources/microsoft-dynamics-gp) |
| Microsoft Dynamics NAV | [Microsoft Dynamics NAV](https://docs.airbyte.com/integrations/sources/microsoft-dynamics-nav) |
| Microsoft Teams | [Microsoft Teams](https://docs.airbyte.com/integrations/sources/microsoft-teams) |
| Mixpanel | [Mixpanel](https://docs.airbyte.com/integrations/sources/mixpanel) |
| Monday | [Monday](https://docs.airbyte.com/integrations/sources/monday) |
| Mongo DB | [Mongo DB](https://docs.airbyte.com/integrations/sources/mongodb-v2) |
| Microsoft SQL Server (MSSQL) | [Microsoft SQL Server (MSSQL)](https://docs.airbyte.com/integrations/sources/mssql) |
| My Hours | [My Hours](https://docs.airbyte.com/integrations/sources/my-hours) |
| MySQL | [MySQL](https://docs.airbyte.com/integrations/sources/mysql) |
| N8n | [N8n](https://docs.airbyte.com/integrations/sources/n8n) |
| NASA | [NASA](https://docs.airbyte.com/integrations/sources/nasa) |
| Oracle Netsuite | [Oracle Netsuite](https://docs.airbyte.com/integrations/sources/netsuite) |
| News API | [News API](https://docs.airbyte.com/integrations/sources/news-api) |
| Newsdata API | [Newsdata API](https://docs.airbyte.com/integrations/sources/newsdata) |
| Notion | [Notion](https://docs.airbyte.com/integrations/sources/notion) |
| New York Times | [New York Times](https://docs.airbyte.com/integrations/sources/nytimes) |
| Okta | [Okta](https://docs.airbyte.com/integrations/sources/okta) |
| Omnisend | [Omnisend](https://docs.airbyte.com/integrations/sources/omnisend) |
| OneSignal | [OneSignal](https://docs.airbyte.com/integrations/sources/onesignal) |
| Open Exchange Rates | [Open Exchange Rates](https://docs.airbyte.com/integrations/sources/open-exchange-rates) |
| OpenWeather | [OpenWeather](https://docs.airbyte.com/integrations/sources/openweather) |
| Opsgenie | [Opsgenie](https://docs.airbyte.com/integrations/sources/opsgenie) |
| Oracle Peoplesoft | [Oracle Peoplesoft](https://docs.airbyte.com/integrations/sources/oracle-peoplesoft) |
| Oracle Siebel CRM | [Oracle Siebel CRM](https://docs.airbyte.com/integrations/sources/oracle-siebel-crm) |
| Oracle DB | [Oracle DB](https://docs.airbyte.com/integrations/sources/oracle) |
| Orb | [Orb](https://docs.airbyte.com/integrations/sources/orb) |
| Orbit | [Orbit](https://docs.airbyte.com/integrations/sources/orbit) |
| Oura | [Oura](https://docs.airbyte.com/integrations/sources/oura) |
| Outreach | [Outreach](https://docs.airbyte.com/integrations/sources/outreach) |
| PagerDuty | [PagerDuty](https://docs.airbyte.com/integrations/sources/pagerduty) |
| Pardot | [Pardot](https://docs.airbyte.com/integrations/sources/pardot) |
| Partnerstack | [Partnerstack](https://docs.airbyte.com/integrations/sources/partnerstack) |
| Paypal Transaction | [Paypal Transaction](https://docs.airbyte.com/integrations/sources/paypal-transaction) |
| Paystack | [Paystack](https://docs.airbyte.com/integrations/sources/paystack) |
| Pendo | [Pendo](https://docs.airbyte.com/integrations/sources/pendo) |
| PersistIq | [PersistIq](https://docs.airbyte.com/integrations/sources/persistiq) |
| Pexels-API | [Pexels-API](https://docs.airbyte.com/integrations/sources/pexels-api) |
| Pinterest | [Pinterest](https://docs.airbyte.com/integrations/sources/pinterest) |
| Pipedrive | [Pipedrive](https://docs.airbyte.com/integrations/sources/pipedrive) |
| Pivotal Tracker | [Pivotal Tracker](https://docs.airbyte.com/integrations/sources/pivotal-tracker) |
| Plaid | [Plaid](https://docs.airbyte.com/integrations/sources/plaid) |
| Plausible | [Plausible](https://docs.airbyte.com/integrations/sources/plausible) |
| Pocket | [Pocket](https://docs.airbyte.com/integrations/sources/pocket) |
| PokéAPI | [PokéAPI](https://docs.airbyte.com/integrations/sources/pokeapi) |
| Polygon Stock API | [Polygon Stock API](https://docs.airbyte.com/integrations/sources/polygon-stock-api) |
| Postgres | [Postgres](https://docs.airbyte.com/integrations/sources/postgres) |
| PostHog | [PostHog](https://docs.airbyte.com/integrations/sources/posthog) |
| Postmarkapp | [Postmarkapp](https://docs.airbyte.com/integrations/sources/postmarkapp) |
| PrestaShop | [PrestaShop](https://docs.airbyte.com/integrations/sources/prestashop) |
| Primetric | [Primetric](https://docs.airbyte.com/integrations/sources/primetric) |
| Public APIs | [Public APIs](https://docs.airbyte.com/integrations/sources/public-apis) |
| Punk-API | [Punk-API](https://docs.airbyte.com/integrations/sources/punk-api) |
| PyPI | [PyPI](https://docs.airbyte.com/integrations/sources/pypi) |
| Qonto | [Qonto](https://docs.airbyte.com/integrations/sources/qonto) |
| Qualaroo | [Qualaroo](https://docs.airbyte.com/integrations/sources/qualaroo) |
| QuickBooks | [QuickBooks](https://docs.airbyte.com/integrations/sources/quickbooks) |
| Railz | [Railz](https://docs.airbyte.com/integrations/sources/railz) |
| RD Station Marketing | [RD Station Marketing](https://docs.airbyte.com/integrations/sources/rd-station-marketing) |
| Recharge | [Recharge](https://docs.airbyte.com/integrations/sources/recharge) |
| Recreation.gov API | [Recreation.gov API](https://docs.airbyte.com/integrations/sources/recreation) |
| Recruitee | [Recruitee](https://docs.airbyte.com/integrations/sources/recruitee) |
| Recurly | [Recurly](https://docs.airbyte.com/integrations/sources/recurly) |
| Redshift | [Redshift](https://docs.airbyte.com/integrations/sources/redshift) |
| Reply.io | [Reply.io](https://docs.airbyte.com/integrations/sources/reply-io) |
| Retently | [Retently](https://docs.airbyte.com/integrations/sources/retently) |
| RingCentral | [RingCentral](https://docs.airbyte.com/integrations/sources/ringcentral) |
| Robert Koch-Institut Covid | [Robert Koch-Institut Covid](https://docs.airbyte.com/integrations/sources/rki-covid) |
| Rocket.chat API | [Rocket.chat API](https://docs.airbyte.com/integrations/sources/rocket-chat) |
| RSS | [RSS](https://docs.airbyte.com/integrations/sources/rss) |
| S3 | [S3](https://docs.airbyte.com/integrations/sources/s3) |
| Salesforce | [Salesforce](https://docs.airbyte.com/integrations/sources/salesforce) |
| Salesloft | [Salesloft](https://docs.airbyte.com/integrations/sources/salesloft) |
| SAP Business One | [SAP Business One](https://docs.airbyte.com/integrations/sources/sap-business-one) |
| sap-fieldglass | [sap-fieldglass](https://docs.airbyte.com/integrations/sources/sap-fieldglass) |
| SearchMetrics | [SearchMetrics](https://docs.airbyte.com/integrations/sources/search-metrics) |
| Secoda API | [Secoda API](https://docs.airbyte.com/integrations/sources/secoda) |
| Sendgrid | [Sendgrid](https://docs.airbyte.com/integrations/sources/sendgrid) |
| Sendinblue API | [Sendinblue API](https://docs.airbyte.com/integrations/sources/sendinblue) |
| Senseforce | [Senseforce](https://docs.airbyte.com/integrations/sources/senseforce) |
| Sentry | [Sentry](https://docs.airbyte.com/integrations/sources/sentry) |
| SFTP Bulk | [SFTP Bulk](https://docs.airbyte.com/integrations/sources/sftp-bulk) |
| SFTP | [SFTP](https://docs.airbyte.com/integrations/sources/sftp) |
| Shopify | [Shopify](https://docs.airbyte.com/integrations/sources/shopify) |
| Shortio | [Shortio](https://docs.airbyte.com/integrations/sources/shortio) |
| Slack | [Slack](https://docs.airbyte.com/integrations/sources/slack) |
| Smaily | [Smaily](https://docs.airbyte.com/integrations/sources/smaily) |
| SmartEngage | [SmartEngage](https://docs.airbyte.com/integrations/sources/smartengage) |
| Smartsheets | [Smartsheets](https://docs.airbyte.com/integrations/sources/smartsheets) |
| Snapchat Marketing | [Snapchat Marketing](https://docs.airbyte.com/integrations/sources/snapchat-marketing) |
| Snowflake | [Snowflake](https://docs.airbyte.com/integrations/sources/snowflake) |
| Sonar Cloud API | [Sonar Cloud API](https://docs.airbyte.com/integrations/sources/sonar-cloud) |
| SpaceX-API | [SpaceX-API](https://docs.airbyte.com/integrations/sources/spacex-api) |
| Spree Commerce | [Spree Commerce](https://docs.airbyte.com/integrations/sources/spree-commerce) |
| Square | [Square](https://docs.airbyte.com/integrations/sources/square) |
| Statuspage.io API | [Statuspage.io API](https://docs.airbyte.com/integrations/sources/statuspage) |
| Strava | [Strava](https://docs.airbyte.com/integrations/sources/strava) |
| Stripe | [Stripe](https://docs.airbyte.com/integrations/sources/stripe) |
| Sugar CRM | [Sugar CRM](https://docs.airbyte.com/integrations/sources/sugar-crm) |
| SurveySparrow | [SurveySparrow](https://docs.airbyte.com/integrations/sources/survey-sparrow) |
| SurveyCTO | [SurveyCTO](https://docs.airbyte.com/integrations/sources/surveycto) |
| SurveyMonkey | [SurveyMonkey](https://docs.airbyte.com/integrations/sources/surveymonkey) |
| Talkdesk Explore | [Talkdesk Explore](https://docs.airbyte.com/integrations/sources/talkdesk-explore) |
| Tempo | [Tempo](https://docs.airbyte.com/integrations/sources/tempo) |
| Teradata | [Teradata](https://docs.airbyte.com/integrations/sources/teradata) |
| The Guardian API | [The Guardian API](https://docs.airbyte.com/integrations/sources/the-guardian-api) |
| TiDB | [TiDB](https://docs.airbyte.com/integrations/sources/tidb) |
| TikTok Marketing | [TikTok Marketing](https://docs.airbyte.com/integrations/sources/tiktok-marketing) |
| Timely | [Timely](https://docs.airbyte.com/integrations/sources/timely) |
| TMDb | [TMDb](https://docs.airbyte.com/integrations/sources/tmdb) |
| Todoist | [Todoist](https://docs.airbyte.com/integrations/sources/todoist) |
| Toggl API | [Toggl API](https://docs.airbyte.com/integrations/sources/toggl) |
| TPL/3PL Central | [TPL/3PL Central](https://docs.airbyte.com/integrations/sources/tplcentral) |
| Trello | [Trello](https://docs.airbyte.com/integrations/sources/trello) |
| TrustPilot | [TrustPilot](https://docs.airbyte.com/integrations/sources/trustpilot) |
| TVMaze Schedule | [TVMaze Schedule](https://docs.airbyte.com/integrations/sources/tvmaze-schedule) |
| Twilio Taskrouter | [Twilio Taskrouter](https://docs.airbyte.com/integrations/sources/twilio-taskrouter) |
| Twilio | [Twilio](https://docs.airbyte.com/integrations/sources/twilio) |
| Twitter | [Twitter](https://docs.airbyte.com/integrations/sources/twitter) |
| Tyntec SMS | [Tyntec SMS](https://docs.airbyte.com/integrations/sources/tyntec-sms) |
| Typeform | [Typeform](https://docs.airbyte.com/integrations/sources/typeform) |
| Unleash | [Unleash](https://docs.airbyte.com/integrations/sources/unleash) |
| US Census API | [US Census API](https://docs.airbyte.com/integrations/sources/us-census) |
| Vantage API | [Vantage API](https://docs.airbyte.com/integrations/sources/vantage) |
| VictorOps | [VictorOps](https://docs.airbyte.com/integrations/sources/victorops) |
| Visma e-conomic | [Visma e-conomic](https://docs.airbyte.com/integrations/sources/visma-economic) |
| Vittally | [Vittally](https://docs.airbyte.com/integrations/sources/vitally) |
| Waiteraid | [Waiteraid](https://docs.airbyte.com/integrations/sources/waiteraid) |
| Weatherstack | [Weatherstack](https://docs.airbyte.com/integrations/sources/weatherstack) |
| Webflow | [Webflow](https://docs.airbyte.com/integrations/sources/webflow) |
| Whisky Hunter | [Whisky Hunter](https://docs.airbyte.com/integrations/sources/whisky-hunter) |
| Wikipedia Pageviews | [Wikipedia Pageviews](https://docs.airbyte.com/integrations/sources/wikipedia-pageviews) |
| WooCommerce | [WooCommerce](https://docs.airbyte.com/integrations/sources/woocommerce) |
| Wordpress | [Wordpress](https://docs.airbyte.com/integrations/sources/wordpress) |
| Workable | [Workable](https://docs.airbyte.com/integrations/sources/workable) |
| Workramp | [Workramp](https://docs.airbyte.com/integrations/sources/workramp) |
| Wrike | [Wrike](https://docs.airbyte.com/integrations/sources/wrike) |
| Xero | [Xero](https://docs.airbyte.com/integrations/sources/xero) |
| XKCD | [XKCD](https://docs.airbyte.com/integrations/sources/xkcd) |
| Yahoo Finance Price | [Yahoo Finance Price](https://docs.airbyte.com/integrations/sources/yahoo-finance-price) |
| Yandex Metrica | [Yandex Metrica](https://docs.airbyte.com/integrations/sources/yandex-metrica) |
| Yotpo | [Yotpo](https://docs.airbyte.com/integrations/sources/yotpo) |
| Younium | [Younium](https://docs.airbyte.com/integrations/sources/younium) |
| YouTube Analytics | [YouTube Analytics](https://docs.airbyte.com/integrations/sources/youtube-analytics) |
| Zapier Supported Storage | [Zapier Supported Storage](https://docs.airbyte.com/integrations/sources/zapier-supported-storage) |
| Zencart | [Zencart](https://docs.airbyte.com/integrations/sources/zencart) |
| Zendesk Chat | [Zendesk Chat](https://docs.airbyte.com/integrations/sources/zendesk-chat) |
| Zendesk Sell | [Zendesk Sell](https://docs.airbyte.com/integrations/sources/zendesk-sell) |
| Zendesk Sunshine | [Zendesk Sunshine](https://docs.airbyte.com/integrations/sources/zendesk-sunshine) |
| Zendesk Support | [Zendesk Support](https://docs.airbyte.com/integrations/sources/zendesk-support) |
| Zendesk Talk | [Zendesk Talk](https://docs.airbyte.com/integrations/sources/zendesk-talk) |
| Zenefits | [Zenefits](https://docs.airbyte.com/integrations/sources/zenefits) |
| Zenloop | [Zenloop](https://docs.airbyte.com/integrations/sources/zenloop) |
| Zoho CRM | [Zoho CRM](https://docs.airbyte.com/integrations/sources/zoho-crm) |
| Zoom | [Zoom](https://docs.airbyte.com/integrations/sources/zoom) |
| Zuora | [Zuora](https://docs.airbyte.com/integrations/sources/zuora) |

## References
- [How to Generate an Access Key Id](https://aws.amazon.com/documentation/access-key-id-generation)  
- [How to Create an S3 Bucket](`https://aws.amazon.com/documentation/create-s3-bucket)  
- [List of All AWS Region Codes](https://aws.amazon.com/documentation/region-codes)


## Legal 

Airbridge is authored un the MIT License.

### License Disclaimer for Contributors

By contributing to this project, you agree to license your contributions under the terms of the project's LICENSE, which is an [MIT License](https://opensource.org/licenses/MIT). This means that your contributions will be available to the public under the same license.

If your contributions include code snippets, files, or other content that is subject to a different license, please provide clear indication of the license terms associated with that content. By making a contribution, you confirm that you have the necessary rights to grant this license.

We appreciate your collaboration and commitment to open source principles. If you have any questions or concerns about licensing, please feel free to contact us.

### License Liability Disclaimer

The contributors to this project, including the project maintainers and collaborators, make every effort to ensure that the project's licensing is accurate and compliant with open-source principles. However, it's important to note that this project may include third-party content, references to products, brands, or software that are subject to different licenses or rights.

While we strive to respect the rights of all content, products, brands, or software, it's possible that certain materials in this project may inadvertently infringe upon the rights of others. If you believe that any content, references, or materials in this project violate your rights or are not appropriately attributed, please let us know immediately so we can address the concern.

Additionally, if you, as a contributor, provide content or contributions that are subject to a different license, or if you reference specific products, brands, or software, you acknowledge and confirm that you have the necessary rights to grant the license under which you are contributing, and that any references are made in accordance with the respective rights holders' terms.

We want to emphasize that any references made to products, brands, or software do not imply any endorsement or affiliation. All products, brands, and software referenced here retain their respective rights. This includes the responsibility to clearly indicate the license terms for any content you contribute.

We value the principles of open collaboration, transparency, and mutual respect within the open-source community. If you have questions or concerns about licensing, attribution, references, or the content of this project, please reach out to us.

Your feedback and vigilance help us maintain the integrity of this project's licensing, references, and its commitment to respecting the rights of all parties involved.
