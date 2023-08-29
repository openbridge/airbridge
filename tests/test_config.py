# Standard library imports
from argparse import Namespace
import json
import os
import sys
import tempfile
from unittest.mock import Mock, MagicMock, patch, mock_open

# Third-party imports
import pytest

# Local application/library specific imports
from airbridge.run import ConfigManager, AirbyteDockerHandler
from airbridge.state import main


CONFIG_FILE_PATH = tempfile.mktemp(suffix=".json")


# Path to a mock configuration file
MOCK_CONFIG_PATH = "mock_config.json"


@pytest.fixture
def mock_default_config():
    return {"default_key": "default_value"}


@pytest.fixture
def mock_cmd_args():
    return Namespace(arg1="value1", arg2="value2")


@pytest.fixture
def mock_config_content():
    return {"config_key": "config_value"}


def test_config_manager_default():
    cm = ConfigManager()
    assert cm.config == {}


def test_config_manager_with_default_config(mock_default_config):
    cm = ConfigManager(default_config=mock_default_config)
    assert cm.config == mock_default_config


def test_config_manager_with_cmd_args(mock_cmd_args):
    cm = ConfigManager(cmd_args=mock_cmd_args)
    assert cm.config == {"arg1": "value1", "arg2": "value2"}


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"config_key": "config_value"}))
def test_config_manager_with_config_file(mock_open_file, mock_config_content):
    cm = ConfigManager(config_file=MOCK_CONFIG_PATH)
    mock_open_file.assert_called_with(MOCK_CONFIG_PATH, "r", encoding="utf-8")
    assert cm.config == mock_config_content


@patch("builtins.open", new_callable=mock_open, read_data="invalid_json_content")
def test_config_manager_with_invalid_config_file(mock_open_file, caplog):
    cm = ConfigManager(config_file=MOCK_CONFIG_PATH)
    mock_open_file.assert_called_with(MOCK_CONFIG_PATH, "r", encoding="utf-8")
    assert "Error decoding JSON from configuration file" in caplog.text
    assert cm.config == {}


@patch("builtins.open", side_effect=FileNotFoundError)
def test_config_manager_with_missing_config_file(mock_open_file, caplog):
    cm = ConfigManager(config_file=MOCK_CONFIG_PATH)
    mock_open_file.assert_called_with(MOCK_CONFIG_PATH, "r", encoding="utf-8")
    assert "Configuration file mock_config.json not found." in caplog.text
    assert cm.config == {}


def test_config_manager_update_from_args(mock_cmd_args):
    cm = ConfigManager()
    cm.update_from_args(mock_cmd_args)
    assert cm.config == {"arg1": "value1", "arg2": "value2"}