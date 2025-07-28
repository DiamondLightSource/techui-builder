from pathlib import Path

import pytest

from techui_builder.builder import Builder
from techui_builder.generate import Generator


@pytest.fixture
def gb():
    b = Builder("./example/create_gui.yaml")
    b._services_dir = Path(f"./example/{b.beamline.dom}-services")
    b._write_directory = Path("example/")
    b._extract_entities(
        ioc_yaml=f"{b._services_dir}/services/{b.components[4].service_name}/config/ioc.yaml",
        component=b.components[4],
    )  # TODO: Change from hardcoded index
    return b


def test_build_groups(gb: Builder):
    generator = Generator(
        gb.entities, gb._gui_map, gb.components[4].name
    )  # TODO: remove hardcoded index
    generator.build_groups()
    with open("./tests/test_files/group.xml") as f:
        control = f.read()
    assert str(generator.group) == control
