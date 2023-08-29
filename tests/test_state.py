import os


import json
from unittest.mock import Mock, patch, ANY
from pathlib import Path
from datetime import datetime, timedelta
from airbridge.run import ConfigManager, AirbyteDockerHandler
from airbridge.state import (
    AirbyteStateHandler,
    ManifestUtility,
    FileUtility,
    StateExtractor,
    parse_arguments,
)


# Update the MockArgs class to include airbyte_src_image attribute
class MockArgs:
    def __init__(self, **entries):
        self.__dict__.update(entries)


sample_args = MockArgs(
    job="mockJob123",
    input="mock_input_path",
    output_path="mock_path",
    src_image="airbyte/mock-image",
    airbyte_src_image="mock_image",
)


def mock_json_file(file_path, content, append=False):
    mode = "a" if append else "w"
    with open(file_path, mode) as f:
        json.dump(content, f)
        f.write("\n")  # Ensure newline after writing content


# FileUtility Class Tests
def test_file_read_success(tmpdir):
    # Given: A file with some content
    file_path = tmpdir.join("sample.txt")
    file_path.write("Sample Content")

    # When: read_file method is called
    content = FileUtility.read_file(str(file_path))

    # Then: The content should match the written content
    assert content == "Sample Content"    # Given: A file with some content
    file_path = tmpdir.join("sample.txt")
    file_path.write("Sample Content")

    # When: read_file method is called
    content = FileUtility.read_file(str(file_path))

    # Then: The content should match the written content
    assert content == "Sample Content"


def test_file_read_failure():
    # Given: A file path that doesn't exist
    file_path = "non_existent_file.txt"

    # When/Then: read_file method is called, it should raise an Exception
    with pytest.raises(Exception, match="Error reading the file"):
        FileUtility.read_file(file_path)


def test_file_write_success(tmpdir):
    # Given: A file path and content to write
    file_path = tmpdir.join("sample_write.txt")
    content = "Sample Write Content"

    # When: write_file method is called
    FileUtility.write_file(str(file_path), content)

    # Then: The file should contain the written content
    assert file_path.read() == content


def test_file_read_failure():
    # Given: A file path that doesn't exist
    file_path = "non_existent_file.txt"

    # When/Then: read_file method is called, it should raise an Exception
    with pytest.raises(Exception, match="Error reading the file"):
        FileUtility.read_file(file_path)

def test_file_write_failure():
    # Given: A non-writable file path (simulated by mocking open method to raise IOError)
    with patch("builtins.open", side_effect=IOError):
        # When/Then: write_file method is called, it should raise an Exception
        with pytest.raises(Exception, match="Error writing to the file"):
            FileUtility.write_file("sample_write_fail.txt", "content")


def test_file_hash_calculation(tmpdir):
    # Given: A file with some content
    file_path = tmpdir.join("sample_hash.txt")
    file_path.write("Sample Hash Content")

    # When: calculate_file_hash method is called
    file_hash = FileUtility.calculate_file_hash(str(file_path))

    # Then: The hash should be a valid SHA-256 hash
    assert len(file_hash) == 64  # SHA-256 hash has 64 characters


# Main Execution Flow Tests


def test_extract_epoch_from_path_valid_input():
    # Given: A valid path with an epoch timestamp
    path = "/path/to/1630368000/data.json"

    # When: _extract_epoch_from_path is called
    extracted_epoch = ManifestUtility._extract_epoch_from_path(path)

    # Then: The extracted epoch should match the provided timestamp
    assert extracted_epoch == 1630368000







