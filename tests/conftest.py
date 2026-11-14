import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_NETWORK") == "1":
        return
    skip = pytest.mark.skip(reason="network test; set RUN_NETWORK=1 to run")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def day():
    return "friday"
