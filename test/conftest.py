import os
import sys

import pytest

# Add the function directory to the Python path
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "lib",
        "bedrock-integration-resolver-py",
        "function",
    )
)
