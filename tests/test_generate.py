from pathlib import Path

import pytest

from techui_builder.builder import Builder
from techui_builder.generate import Generator


@pytest.fixture
def gb():
    b = Builder(Path("example/create_gui.yaml"))
    b._services_dir = Path(f"./example/{b.beamline.dom}-services")
    b._write_directory = Path("example/")
    b._extract_entities(
        ioc_yaml=Path(f"{b._services_dir}/services/bl01t-mo-ioc-01/config/ioc.yaml"),
    )  # TODO: Change from hardcoded index
    return b


def test_build_groups(gb: Builder):
    generator = Generator(
        gb.entities["BL01T-MO-MAP-01:STAGE"], gb.components[4].name, Path("./")
    )  # TODO: remove hardcoded index
    generator.build_groups()
    print(generator.group)
    print("------------HERE-------------")
    with open("./tests/test_files/group.xml") as f:
        control = f.read()
    assert str(generator.group) == control
