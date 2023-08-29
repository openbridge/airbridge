# Standard library imports
import json
from unittest.mock import MagicMock, patch

# Related third-party imports
import pytest

# Local application/library specific imports
from airbridge.run import AirbyteDockerHandler


# Define some constant values
TEST_CONFIG = {
    "job": "test_job",
    "catalog_loc": "/path/to/catalog.json",
    "src_config_loc": "/path/to/src/config.json",
    "dst_config_loc": "/path/to/dst/config.json",
}
TEST_OUTPUT_PATH = "/path/to/output"
TEST_SRC_IMAGE = "test_src_image"
TEST_DST_IMAGE = "test_dst_image"

@pytest.fixture
def mock_docker_client():
    """Returns a mocked Docker client."""
    client = MagicMock()
    client.ping.return_value = True
    client.containers.get.return_value = MagicMock()
    return client

@pytest.fixture
def handler(mock_docker_client, mocker):
    """Returns a fresh instance of the AirbyteDockerHandler."""
    mocker.patch("os.makedirs", return_value=None)  # Mock directory creation
    with patch("docker.from_env", return_value=mock_docker_client):
        return AirbyteDockerHandler(
            configuration=TEST_CONFIG,
            output_path=TEST_OUTPUT_PATH,
            src_image=TEST_SRC_IMAGE,
            dst_image=TEST_DST_IMAGE
        )

def test_init(handler):
    assert handler.configuration == TEST_CONFIG
    assert handler.output_path == TEST_OUTPUT_PATH
    assert handler.src_image == TEST_SRC_IMAGE
    assert handler.dst_image == TEST_DST_IMAGE
    assert handler.job_id == TEST_CONFIG["job"]

def test_sanitize_container_name():
    assert AirbyteDockerHandler.sanitize_container_name("name@with*weird^chars") == "name_with_weird_chars"

def test_load_config_from_file(handler, tmpdir):
    config_file = tmpdir.join("config.json")
    test_data = {"key": "value"}
    config_file.write(json.dumps(test_data))
    handler.load_config_from_file(str(config_file))
    assert handler.configuration["key"] == "value"

def test_load_config_from_args(handler):
    class MockArgs:
        arg1 = "value1"
        arg2 = "value2"

    handler.load_config_from_args(MockArgs)
    assert handler.configuration["arg1"] == "value1"
    assert handler.configuration["arg2"] == "value2"

def test_create_check_command(handler):
    assert handler.create_check_command() == "check --config /secrets/config.json"

def test_initialize_docker_client_success(mock_docker_client):
    with patch("docker.from_env", return_value=mock_docker_client):
        client = AirbyteDockerHandler._initialize_docker_client(AirbyteDockerHandler())
        assert client.ping() == True

def test_check_docker_availability_true(handler):
    assert handler.check_docker_availability() == True

def test_check_image_provided(handler):
    assert handler.check_image_provided(TEST_SRC_IMAGE, "Source") == True
    assert handler.check_image_provided(None, "Source") == False

@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("/path/to/output", True),
        ("/path/with/permission/error", False),
    ],
)
def test_execute(handler, mock_docker_client, test_input, expected):
    handler.output_path = test_input

    with patch.object(handler, "pull_docker_image") as mock_pull, \
            patch.object(handler, "_prepare_src_volumes") as mock_src_volumes, \
            patch.object(handler, "_prepare_dst_volumes") as mock_dst_volumes, \
            patch.object(handler, "run_image_check") as mock_image_check, \
            patch.object(handler, "_run_container_with_entrypoint") as mock_run_container:

        mock_pull.return_value = None
        mock_image_check.return_value = None
        mock_run_container.return_value = None

        # Simulate a volume preparation error for the specific input
        if test_input == "/path/with/permission/error":
            mock_src_volumes.side_effect = Exception("Permission error")
            mock_dst_volumes.side_effect = Exception("Permission error")
        else:
            mock_src_volumes.return_value = {}
            mock_dst_volumes.return_value = {}

        assert handler.execute() == expected

def test_final_cleanup(handler):
    handler.active_containers = ["container1", "container2"]
    with patch.object(handler, "cleanup_container", side_effect=[True, False]):
        handler.final_cleanup()
        assert handler.active_containers == ["container2"]
