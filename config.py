#!/usr/bin/env python3

import requests
import json
import yaml
import argparse
import os
import logging
import warnings

warnings.simplefilter(action='ignore', category=DeprecationWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 3

# Define the custom warning class for config validation
class ConfigValidationWarning(UserWarning):
    pass

def is_url(s):
    """Check if the string is a URL."""
    return s.startswith('http://') or s.startswith('https://')


def get_content(source):
    """Get content from either a URL or a local file path."""
    if is_url(source):
        for _ in range(RETRY_ATTEMPTS):
            try:
                response = requests.get(source, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException:
                logger.warning(f"Failed to fetch content from {source}. Retrying...")
        raise RuntimeError(f"Failed to fetch content from {source} after {RETRY_ATTEMPTS} attempts.")
    else:
        with open(source, 'r') as file:
            return file.read()
        
def download_and_parse_spec(source):
    """Download the spec file from the given URL or read from a local path and return its parsed content."""
    content = None
    
    if is_url(source):
        for _ in range(RETRY_ATTEMPTS):
            try:
                response = requests.get(source, timeout=10)
                response.raise_for_status()
                content = response.text
                break
            except requests.ConnectionError:
                logger.warning(f"Failed to establish a connection to {source}. Retrying...")
            except requests.Timeout:
                logger.warning(f"Request to {source} timed out. Retrying...")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch the spec from {source}. Error: {e}")
                break
    else:
        try:
            with open(source, 'r') as file:
                content = file.read()
        except Exception as e:
            logger.error(f"Failed to read the spec from {source}. Error: {e}")
            raise RuntimeError(f"Failed to read the spec from {source}.")
    
    if content:
        try:
            is_yaml = source.endswith((".yaml", ".yml"))
            if is_yaml:
                return yaml.safe_load(content)
            else:
                return json.loads(content)
        except (yaml.YAMLError, json.JSONDecodeError):
            logger.error(f"Failed to parse the spec content from {source}.")
            raise RuntimeError(f"Failed to parse the spec content from {source}.")

    raise RuntimeError(f"Failed to fetch and parse the spec from {source} after {RETRY_ATTEMPTS} attempts.")

def is_writable(path):
    """Check if the given path is writable."""
    if os.path.exists(path):
        if os.path.isfile(path):
            return os.access(path, os.W_OK)
        else:  # path is a directory
            # check if we can write to that directory by creating a temporary file
            temp_filename = os.path.join(path, ".temp_write_check")
            try:
                with open(temp_filename, 'w') as temp_file:
                    temp_file.write("test")
                os.remove(temp_filename)
                return True
            except Exception:
                return False
    else:  # if path doesn't exist, we check the parent directory for write access
        parent_dir = os.path.dirname(path)
        if parent_dir:  # if path has a parent directory, check its write access recursively
            return is_writable(parent_dir)
        else:  # path is relative and has no parent directory, so we check the current working directory
            return True

def extract_fields_with_type(data, required_fields=[]):
    """Recursively extract fields from the spec data and denote if they are required or optional."""
    fields = {}
    if not isinstance(data, dict):
        return fields
    properties = data.get("properties", {})
    for field, attributes in properties.items():
        if 'properties' in attributes:
            nested_fields = extract_fields_with_type(attributes, attributes.get("required", []))
            fields[field] = nested_fields
        elif 'oneOf' in attributes:
            # Combine all properties under 'oneOf' into a single dictionary and extract fields from it
            combined_properties = {}
            for option in attributes['oneOf']:
                combined_properties.update(option.get('properties', {}))
            nested_fields = extract_fields_with_type({"properties": combined_properties}, required_fields)
            fields[field] = nested_fields
        elif field in required_fields:
            fields[field] = "required_value"
        else:
            fields[field] = "optional_value"
    return fields

def get_output_filename_from_title(title, default_name='config.json'):
    """Generate a filename based on the spec title."""
    return title.lower().replace(" ", "-") + "-config.json" if title else default_name

def generate_config_file(fields, spec_title, output_path=None):
    """Generate a config.json file with "required_value" or "optional_value" for the fields."""
    output_path = output_path or get_output_filename_from_title(spec_title)
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, get_output_filename_from_title(spec_title))
    with open(output_path, 'w') as file:
        json.dump(fields, file, indent=4)
    print(f"config.json file generated at {output_path}!")

def download_and_save_file(source, output_path):
    """Download content from the source (URL or local path) and save it to the output_path."""
    
    # Determine if source is a URL or a local file path and get content accordingly
    if is_url(source):
        response = requests.get(source, timeout=10)
        response.raise_for_status()
        content = response.content
    else:
        with open(source, 'rb') as file:
            content = file.read()
    
    # Save the content to the specified output_path
    if os.path.isdir(output_path):
        output_filename = os.path.basename(source)
        output_path = os.path.join(output_path, output_filename)
    with open(output_path, 'wb') as file:
        file.write(content)
    
    print(f"File saved to {output_path}!")


def main():
    parser = argparse.ArgumentParser(description="Generate a config.json file based on the provided spec URL or local path.")
    
    # Updated help description
    parser.add_argument('-i', '--input', help='URL or local path to the spec file (either .json or .yaml/.yml)')
    parser.add_argument('-o', '--output', default=None, help='Output path for the generated config.json file')
    
    # Updated help description for the -c argument
    parser.add_argument('-c', '--catalog-url', help='URL or local path to a json or yaml file to be downloaded/saved directly')
    
    args = parser.parse_args()
    
    if args.catalog_url:
        download_and_save_file(args.catalog_url, args.output if args.output else ".")
        return
    
    # Rest of the logic remains unchanged
    spec_data = download_and_parse_spec(args.input)
    if "connectionSpecification" not in spec_data:
        raise ValueError("The spec doesn't seem to have a 'connectionSpecification' key.")
    if args.output and not is_writable(args.output):
        raise PermissionError(f"Do not have write permissions for the path: {args.output}")
    spec_title = spec_data.get("connectionSpecification", {}).get("title", "default")
    fields = extract_fields_with_type(spec_data["connectionSpecification"], spec_data["connectionSpecification"].get("required", []))
    generate_config_file(fields, spec_title, args.output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, PermissionError) as e:
        logger.error(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
