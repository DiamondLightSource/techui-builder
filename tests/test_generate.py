from pathlib import Path

import pytest

from techui_builder.builder import Builder
from techui_builder.generate import Generator


@pytest.fixture
def gen():
    b = Builder(Path("example/create_gui.yaml"))
    b._services_dir = Path(f"./example/{b.beamline.dom}-services")
    b._write_directory = Path("example/")
    b._extract_entities(
        ioc_yaml=Path(f"{b._services_dir}/services/bl01t-mo-ioc-01/config/ioc.yaml"),
    )  # TODO: Change from hardcoded index
    gen = Generator(
        b.entities["BL01T-MO-MAP-01:STAGE"], b.components[4].name, Path("./")
    )
    return gen


def test_create_widget(gen: Generator):
    with open("./tests/test_files/widget.xml") as f:
        control = f.read()
    assert str(gen._create_widget(gen.screen_components[1])) == control


def test_write_screen(gen: Generator):
    gen.build_groups()
    gen.write_screen(Path("./"))
    with open("./motor.bob") as f:
        expected = f.read()

    with open("./tests/test_files/screen.bob") as f:
        control = f.read()

    assert expected == control


def test_build_groups(gen: Generator):
    gen.build_groups()
    with open("./tests/test_files/group.xml") as f:
        control = f.read()
    assert str(gen.group) == control
