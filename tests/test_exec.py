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
from airbridge.run import StateHandler, AirbyteDockerHandler, handle_docker, handle_state

def test_handle_docker_success():
    mock_args = Mock()
    mock_args.state_file_path = "test_state_path"
    mock_args.output_path = "test_output_path"
    mock_args.airbyte_src_image = "test_src_image"
    mock_args.airbyte_dst_image = "test_dst_image"
    
    # Mock src_runtime for the context of this test
    mocked_src_runtime = "test_runtime"
    
    with patch("airbridge.run.AirbyteDockerHandler") as mock_handler, \
         patch("logging.info") as mock_log_info, \
         patch("airbridge.run.src_runtime", mocked_src_runtime):  # Mocking the src_runtime used within handle_docker
        result = handle_docker(mock_args)
        
    # Assert the order of log messages
    mock_log_info.assert_any_call("🚀 Initiating your Airbridge data workflow...")
    mock_log_info.assert_any_call("A state file was passed: test_state_path")
    mock_handler.assert_called_with(
        configuration=vars(mock_args),
        output_path="test_output_path",
        src_image="test_src_image",
        dst_image="test_dst_image",
        src_runtime=mocked_src_runtime,  # Use the mocked value here
    )
    assert result is not None

def test_handle_docker_failure():
    mock_args = Mock()
    mock_args.state_file_path = "test_state_path"
    
    with patch("logging.info") as mock_log_info, \
         patch("logging.error") as mock_log_error, \
         patch("airbridge.run.AirbyteDockerHandler", side_effect=Exception("Test error")):
        result = handle_docker(mock_args)
    
    # Adjust the expected log message
    mock_log_info.assert_called_with("A state file was passed: test_state_path")
    mock_log_error.assert_called_with("Error encountered of type <class 'Exception'>: Test error")
    assert result is None

def test_handle_state_success():
    mock_args = Mock()
    mock_args.output_path = "test_output_path"
    mock_args.airbyte_src_image = "test_src_image"
    mock_args.source_config_hash = "test_hash"
    
    with patch("airbridge.run.StateHandler") as mock_state_handler:
        handle_state(mock_args)
        
    mock_state_handler.assert_called_with(
        output_path="test_output_path",
        airbyte_src_image="test_src_image",
        source_config_hash="test_hash",
        job_id=getattr(mock_args, "job", None),
    )
    mock_state_handler.return_value.execute.assert_called_once()

def test_handle_state_failure():
    mock_args = Mock()
    
    with patch("airbridge.run.StateHandler", side_effect=Exception("Test error")), \
         patch("logging.error") as mock_log_error:
        with pytest.raises(RuntimeError, match="Failed executing state script."):
            handle_state(mock_args)
            
    mock_log_error.assert_called_with("Error executing state script of type <class 'Exception'>: Test error")
