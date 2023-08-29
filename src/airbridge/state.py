#!/usr/bin/env python3

"""This script handles the initialization and output of Airbyte state."""

import hashlib
import json
import logging
import os
import re
from datetime import datetime


# ==========================
# FileUtility
# ==========================
class FileUtility:
    """Utility class for handling file operations such as reading, writing, and
    calculating file hash."""

    @staticmethod
    def read_file(file_path: str) -> str:
        """Read the content of a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: Content of the file.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except IOError as exc:
            raise Exception(f"Error reading the file {file_path}.") from exc

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        """Write content to a file.

        Args:
            file_path (str): Path to the file.
            content (str): Content to be written.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
        except IOError as exc:
            raise Exception(f"Error writing to the file {file_path}.") from exc

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate the SHA-256 hash of a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: SHA-256 hash of the file.
        """
        try:
            with open(file_path, "rb") as file:
                file_bytes = file.read()
                file_hash = hashlib.sha256(file_bytes).hexdigest()
            return file_hash
        except FileNotFoundError as exc:
            raise Exception(f"File {file_path} not found.") from exc
        except IOError as exc:
            raise Exception(f"Error reading the file {file_path}.") from exc


# ==========================
# StateExtractor
# ==========================


class StateExtractor:
    @staticmethod
    def extract_state_from_data(data, test_state=None):
        """Extract state from a list of JSON strings.

        Args:
            data (list or dict): List of JSON strings or a single JSON object.
            test_state (dict, optional): Test state to return for unit testing purposes.

        Returns:
            dict: Extracted state from the provided data.
        """
        final_state = {}

        if isinstance(data, dict):
            obj = data
        else:
            for line in data:
                try:
                    obj = json.loads(line)

                    if "state" in obj:
                        stream_name = obj["state"]["stream"][
                            "stream_descriptor"
                        ]["name"]
                        stream_data = obj["state"]["data"].get(stream_name, {})

                        if not stream_data:
                            stream_data = {"created": 0}

                        if stream_name not in final_state or final_state[
                            stream_name
                        ].get("created", 0) < stream_data.get("created", 0):
                            final_state[stream_name] = stream_data
                except json.JSONDecodeError as exc:
                    raise Exception(f"Error decoding JSON: {line}") from exc


        return final_state if test_state is None else test_state

    @staticmethod
    def save_state_to_file(final_state, filename):
        """Save the given state to a JSON file.

        Args:
            final_state (dict): State to be saved.
            filename (str): Path to the file where the state will be saved.

        Returns:
            str: Path to the saved state file.

        Raises:
            Exception: If there is an error writing to the file.
        """
        try:
            dir_structure = os.path.dirname(filename)
            if not os.path.exists(dir_structure):
                os.makedirs(dir_structure)
                logging.info("Created directory: %s", dir_structure)
            state_file_path = os.path.join(dir_structure, "state.json")
            with open(state_file_path, "w", encoding="utf-8") as outfile:
                json.dump(final_state, outfile, indent=2)
            return state_file_path
        except IOError as exc:
            raise Exception(f"Error writing to the state file at {state_file_path}") from exc



# ==========================
# ManifestUtility
# ==========================


class ManifestUtility:
    """Utility class for generating and saving manifest content."""

    @staticmethod
    def _extract_epoch_from_path(path):
        """Extracts the directory name (epoch value) just before the filename
        in a given path.

        Args:
            path (str): The path from which to extract the epoch value.

        Returns:
            int: The extracted epoch value.
        """
        epoch_value = os.path.basename(os.path.dirname(path))
        logging.info(f"Extracted epoch value from path: {epoch_value}")
        return int(epoch_value)

    @staticmethod
    def generate_manifest_content(
        state_file_path, key_value, airbyte_src_image, job_id, data_file_path
    ):
        """Generate manifest content with error handling."""
        try:
            src_runtime = ManifestUtility._extract_epoch_from_path(
                state_file_path
            )
            manifest_content = {
                key_value: [
                    {
                        "jobid": job_id,
                        "source": airbyte_src_image,
                        "data_file": data_file_path,
                        "state_file_path": state_file_path,
                        "timestamp": int(src_runtime),
                        "modified_at": int(datetime.now().timestamp()),
                    }
                ]
            }
            logging.info(f"Generated manifest content: {manifest_content}")
            return manifest_content
        except Exception as exc:
            logging.error(f"Error generating manifest content: {str(exc)}")
            raise Exception(
                f"Error generating manifest content: {str(exc)}"
            ) from exc

    @staticmethod
    def save_manifest_content(manifest_content: dict) -> None:
        """Saves the provided manifest content into the manifest file, merging
        with existing content if present."""

        manifest_dir = os.getcwd()

        # Ensure the manifest directory exists
        if not os.path.exists(manifest_dir):
            os.makedirs(manifest_dir)

        manifest_file_path = os.path.join(manifest_dir, "manifest.json")

        # Initialize an empty dictionary for existing manifest content
        existing_manifest_content = {}

        try:
            # Check if manifest file exists and read its content
            if os.path.exists(manifest_file_path):
                with open(manifest_file_path, "r", encoding="utf-8") as manifest_file:
                    file_content = manifest_file.read().strip()
                    if file_content:  # Check if the file has content
                        existing_manifest_content = json.loads(file_content)
                    else:
                        logging.warning(
                            "Manifest file %s is empty. Initializing with an empty dictionary.",
                            manifest_file_path,
                        )
            else:
                logging.info(
                    "Manifest file %s not found. A new one will be created.",
                    manifest_file_path,
                )

            # Merge new manifest content with existing content
            for key, new_records in manifest_content.items():
                existing_manifest_content.setdefault(key, []).extend(new_records)

            # Save merged manifest content
            with open(manifest_file_path, "w", encoding="utf-8") as manifest_file:
                json.dump(existing_manifest_content, manifest_file, indent=2)
                logging.info("Manifest content saved to %s", manifest_file_path)

        except json.JSONDecodeError:
            logging.error(
                "Error decoding JSON from the manifest file %s.",
                manifest_file_path,
            )
            raise
        except PermissionError:
            logging.error(
                "Permission denied when trying to access the directory %s or file %s.",
                manifest_dir,
                manifest_file_path,
            )
            raise
        except IOError as exc:
            logging.error(
                "Error writing to the manifest file %s. Details: %s",
                manifest_file_path,
                exc,
            )
            raise


# ==========================
# AirbyteStateHandler
# ==========================


class AirbyteStateHandler:
    """Handler for processing Airbyte state files and generating manifest
    content."""

    def __init__(
        self,
        manifest_base_path,
        output_path,
        airbyte_src_image,
        job_id=None,
        src_runtime=None,
        config_hash=None,
    ):
        self.manifest_base_path = manifest_base_path
        self.output_path = output_path
        self.airbyte_src_image = airbyte_src_image
        self.job_id = job_id
        self.src_runtime = (
            src_runtime  # Storing src_runtime for use in the class
        )
        self.config_hash = config_hash
        # Preprocess the airbyte_src_image to replace underscores and slashes with dashes
        self.airbyte_src_image = airbyte_src_image.replace("_", "-").replace(
            "/", "-"
        )

        logging.info(
            "Initialized AirbyteStateHandler with output_path: %s",
            self.output_path,
        )

    def process_data_file(self, filename):
        """Process a given data file and save its state."""
        logging.info("Processing data file: %s", filename)

        try:
            # Process the file and extract the final state
            key_value = self._get_key_value()

            with open(filename, "r", encoding="utf-8") as file:
                data = file.readlines()
            final_state = StateExtractor.extract_state_from_data(data)
            state_file_path = StateExtractor.save_state_to_file(
                final_state, filename
            )
            logging.info("Saved state to: %s", state_file_path)

            key_value = self._get_key_value()
            manifest_content = ManifestUtility.generate_manifest_content(
                state_file_path=state_file_path,
                key_value=key_value,
                airbyte_src_image=self.airbyte_src_image,
                job_id=self.job_id,
                data_file_path=filename,  # Passing the filename as the data_file_path
            )
            manifest_base = self.airbyte_src_image
            manifest_dir = os.path.join(
                self.manifest_base_path, "states", manifest_base
            )

            ManifestUtility.save_manifest_content(manifest_content)
            logging.info("Saved manifest content to: %s", manifest_dir)

            return final_state
        except Exception as error:
            logging.error(
                "Error processing data file %s: %s", filename, str(error)
            )
            raise

    def _extract_state_from_file(self, filename):
        """Extract state from a given file."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = file.readlines()
            return StateExtractor.extract_state_from_data(data)
        except Exception as error:
            logging.error(
                "Error processing data file %s: %s", filename, str(error)
            )
            raise

    def _save_final_state(self, final_state, filename):
        """Save the final state to a file and return its path."""
        return StateExtractor.save_state_to_file(final_state, filename)

    def _get_key_value(self):
        """Get the key value which is always the job_id."""
        return self.config_hash if self.config_hash else self.output_path

    def traverse_and_process(self):
        """Traverse the search path and process each data file."""
        # Set the search path as output_path + airbyte_src_image
        search_path = self.output_path
        logging.info("Starting traversal from search path: %s", search_path)

        data_pattern = re.compile(rf"data_{self.src_runtime}\.json")
        data_found = False  # Variable to track if data file(s) was/were found

        try:
            logging.debug("Searching in directory: %s", search_path)

            for subdir, _, files in os.walk(search_path):
                logging.debug("Checking subdir: %s", subdir)

                for file in files:
                    if data_pattern.match(file):
                        data_file_path = os.path.join(
                            subdir, file
                        )  # Define data_file_path here
                        self.process_data_file(data_file_path)
                        data_found = True
                        logging.info(f"Found {file} at: {data_file_path}")

            if not data_found:
                logging.warning(
                    "No matching 'data_\\d+.json' files found."
                )
        except Exception as error:
            logging.error(
                "Error traversing and processing directory %s: %s",
                search_path,
                str(error),
            )
            raise


# Main Execution and Helpers
def parse_arguments(
    src_runtime, input_path, airbyte_src_image, job_id=None, config_hash=None
):
    """Parse and return arguments directly."""
    args = {
        "src_runtime": src_runtime,
        "input_path": input_path,  # Adjust the key name here
        "airbyte_src_image": airbyte_src_image,
        "job": job_id,
        "config_hash": config_hash,
    }
    return args


def process_airbyte_state(
    src_runtime, input_path, airbyte_src_image, job_id=None, config_hash=None
):
    """Process the Airbyte state given the input path, Airbyte source image,
    and an optional job ID.

    Args:
        input_path (str): Path to the directory containing data.json.
        airbyte_src_image (str): Source Airbyte image.
        job_id (str, optional): Job ID. Defaults to None.
    """
    handler = AirbyteStateHandler(
        manifest_base_path=input_path,
        output_path=input_path,
        airbyte_src_image=airbyte_src_image,
        job_id=job_id,
        src_runtime=src_runtime,
        config_hash=config_hash,
    )
    handler.traverse_and_process()


def main(
    src_runtime, input_path, airbyte_src_image, job_id=None, config_hash=None
):
    """Main execution function."""
    args = {
        "src_runtime": src_runtime,
        "input_path": input_path,
        "airbyte_src_image": airbyte_src_image,
        "job_id": job_id,
        "config_hash": config_hash,
    }
    process_airbyte_state(**args)
