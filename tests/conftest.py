from pathlib import Path

import pytest

from techui_builder.builder import Builder, json_map


@pytest.fixture
def builder():
    path = Path("example/t01-services/synoptic/techui.yaml")
    b = Builder(path)
    b._services_dir = Path("example/t01-services/services")
    b._write_directory = b._services_dir.parent.joinpath("synoptic/opis")
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
