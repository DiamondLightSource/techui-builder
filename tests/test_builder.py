import os
from pathlib import Path

import pytest

from techui_builder.builder import Builder


@pytest.fixture
def gb():
    b = Builder("./example/create_gui.yaml")
    return b


def test_guibuilder(gb: Builder):
    assert gb.beamline.dom == "bl01t"
    assert gb.beamline.desc == "Test Beamline"
    assert gb.components[0].name == "fshtr"
    assert gb.components[0].desc == "Fast Shutter"
    assert gb.components[0].P == "BL01T-EA-FSHTR-01"
    assert gb.components[0].R is None
    assert gb.components[0].attribute is None
    assert gb.components[4].name == "motor"
    assert gb.components[4].desc == "Hexapod Stage"
    assert gb.components[4].P == "BL01T-MO-MAP-01"
    assert gb.components[4].R == "STAGE"
    assert gb.components[4].attribute is None
    assert gb.components[4].service_name == "bl01t-mo-ioc-01"


def test_gb_extract_entities(gb):
    gb._extract_entities(
        ioc_yaml=f"example/{gb._services_dir}/services/{gb.components[4].service_name}/config/ioc.yaml",
        component=gb.components[4],
    )

    assert gb.entities[0].type == "pmac.GeoBrick"
    assert gb.entities[0].desc == "Hexapod Stage"
    assert gb.entities[0].P == "BL01T-MO-BRICK-01"
    assert gb.entities[0].M is None
    assert gb.entities[0].R is None
    assert gb.entities[1].type == "pmac.autohome"
    assert gb.entities[1].desc == "Hexapod Stage"
    assert gb.entities[1].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[1].M is None
    assert gb.entities[1].R is None
    assert gb.entities[2].type == "pmac.dls_pmac_asyn_motor"
    assert gb.entities[2].desc == "Hexapod Stage"
    assert gb.entities[2].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[2].M == "X"
    assert gb.entities[2].R is None
    assert gb.entities[3].type == "pmac.dls_pmac_asyn_motor"
    assert gb.entities[3].desc == "Hexapod Stage"
    assert gb.entities[3].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[3].M == "A"
    assert gb.entities[3].R is None


def test_setup(gb):
    gb._services_dir = Path(f"./example/{gb.beamline.dom}-services")
    gb._write_directory = Path("example/")
    gb.setup()

    with open(f"./{gb._write_directory}/motor.bob") as f:
        expected = f.read()

    with open("./tests/test_files/motor.bob") as f:
        control = f.read()

    assert expected == control
    if os.path.exists(f"./{gb._write_directory}/motor.bob"):
        os.remove(f"./{gb._write_directory}/motor.bob")
