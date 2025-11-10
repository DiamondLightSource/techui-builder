from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from techui_builder.builder import Builder, json_map
from techui_builder.generate import Generator


@pytest.fixture
def builder():
    ixx_services = Path(__file__).parent.parent.joinpath(Path("example/t01-services"))
    techui_path = ixx_services.joinpath("synoptic/techui.yaml")

    with patch("techui_builder.builder.Generator") as mock_generator:
        mock_generator.return_value = MagicMock()

        b = Builder(techui_path)
        b._services_dir = ixx_services.joinpath("services")
        b._write_directory = ixx_services.joinpath("synoptic/opis")
        return b


@pytest.fixture
def builder_with_setup(builder: Builder):
    builder.setup()
    return builder


@pytest.fixture
def example_json_map():
    # Create test json map with child json map
    test_map_child = json_map("test_child_bob.bob", exists=False)
    test_map = json_map("tests/test_files/test_bob.bob")
    test_map.children.append(test_map_child)

    return test_map


@pytest.fixture
def generator():
    g = Generator(Path("example/t01-services"))

    return g
