from pathlib import Path

import pytest

from techui_builder.builder import Builder


@pytest.fixture
def builder():
    path = Path("example/t01-services/synoptic/techui.yaml")
    b = Builder(path)
    b._services_dir = Path("example/t01-services/services")
    b._write_directory = b._services_dir.parent.joinpath("synoptic/opis")
    return b
