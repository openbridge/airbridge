import os
import sys

import io
import json
import orjson
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

from airbridge.run import ConfigManager, AirbyteDockerHandler
from airbridge.state import main

Path("tmp/tests/").mkdir(parents=True, exist_ok=True)

def test_pub_apis_sync():
    """Run a sync using the Airbyte source for public APIs.
    """

    # Define the volume mapping in the expected format
    volumes_mapping = {"/tmp/tests/": {"bind": "/output", "mode": "rw"}}

    dh = AirbyteDockerHandler(
        configuration={
            "image": "airbyte/source-public-apis",
            "volumes": volumes_mapping,
        },
        output_path="tmp/tests/",  # This is where the output on the host machine will be stored
    )

    # Run the image and check if it executes successfully
    # Note: Ensure that the `run_image_check` method writes the output to the `/output` directory in the container
    dh.run_image_check("airbyte/source-public-apis:0.1.0", volumes_mapping)

