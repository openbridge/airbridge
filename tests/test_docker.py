
import os
import sys
import json
from unittest.mock import patch, Mock, MagicMock
from argparse import Namespace
from airbridge.run import ConfigManager, AirbyteDockerHandler
from airbridge.state import main
import tempfile
import docker


# The path to a sample config file for testing purposes
CONFIG_FILE_PATH = tempfile.mktemp(suffix=".json")


@pytest.fixture
def sample_config_file():
    # Creating a sample config file for testing
    config_data = {"key1": "value1", "key2": "value2"}
    with open(CONFIG_FILE_PATH, "w") as file:
        json.dump(config_data, file)
    return CONFIG_FILE_PATH


def test_config_manager_default():
    cm = ConfigManager()
    assert cm.config == {}


def test_config_manager_with_default_config():
    default_config = {"default_key": "default_value"}
    cm = ConfigManager(default_config=default_config)
    assert cm.config == default_config


def test_config_manager_with_cmd_args():
    cmd_args = Namespace(arg1="value1", arg2="value2")
    cm = ConfigManager(cmd_args=cmd_args)
    assert cm.config == {"arg1": "value1", "arg2": "value2"}


def test_docker_availability_true():
    with patch("docker.from_env") as mock_docker:
        # Mocking the ping method to simulate that Docker is available
        mock_docker.return_value.ping.return_value = True
        dh = AirbyteDockerHandler()
        assert dh.check_docker_availability() == True


def test_create_check_command():
    dh = AirbyteDockerHandler(configuration={}, output_path="")
    command = dh.create_check_command()
    assert command == "check --config /secrets/config.json"


@patch("airbridge.run.json.load")
@patch("builtins.open")
def test_load_config_from_file(mock_open, mock_json_load):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_json_load.return_value = {"key": "value"}

    dh = AirbyteDockerHandler(configuration={}, output_path="")
    dh.load_config_from_file("/path/to/config.json")
    assert dh.configuration == {"key": "value"}


@patch("airbridge.run.docker.from_env")
def test_pull_docker_image(mock_docker):
    dh = AirbyteDockerHandler(configuration={}, output_path="")
    dh.pull_docker_image("image_name:tag")
    mock_docker.return_value.images.pull.assert_called_with("image_name:tag")
