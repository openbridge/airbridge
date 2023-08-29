import os
import sys
import json
from argparse import Namespace
from unittest.mock import Mock, MagicMock, patch
from airbridge.run import ConfigManager, AirbyteDockerHandler
from airbridge.state import main
import tempfile

CONFIG_FILE_PATH = tempfile.mktemp(suffix=".json")


@pytest.fixture
def sample_config_file():
    # Creating a sample config file for testing
    config_data = {"key1": "value1", "key2": "value2"}
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
        json.dump(config_data, file)
        file_path = file.name
    yield file_path
    os.remove(file_path)


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


