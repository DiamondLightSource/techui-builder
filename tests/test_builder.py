import os
from pathlib import Path

import pytest

from techui_builder.builder import Builder


@pytest.fixture
def gb():
    path = Path("example/create_gui.yaml")
    b = Builder(path)
    b._services_dir = Path("./example/bl01t-services/services")
    b.setup()
    return b


@pytest.mark.parametrize(
    "attr, expected",
    [
        ("beamline.dom", "bl01t"),
        ("beamline.desc", "Test Beamline"),
    ],
)
def test_beamline_attributes(gb: Builder, attr, expected):
    assert eval(f"gb.{attr}") == expected


@pytest.mark.parametrize(
    "index, name, desc, P, R, attribute, extras",
    [
        (0, "fshtr", "Fast Shutter", "BL01T-EA-FSHTR-01", None, None, None),
        (
            4,
            "motor",
            "Hexapod Stage",
            "BL01T-MO-MAP-01",
            "STAGE",
            None,
            None,
        ),
    ],
)
def test_component_attributes(gb: Builder, index, name, desc, P, R, attribute, extras):
    component = gb.components[index]
    assert component.name == name
    assert component.desc == desc
    assert component.P == P
    assert component.R == R
    assert component.attribute == attribute
    if extras is not None:
        assert component.extras == extras


@pytest.mark.parametrize(
    "index, type, desc, P, M, R",
    [
        (0, "pmac.GeoBrick", None, "BL01T-MO-BRICK-01", None, None),
        (0, "pmac.autohome", None, "BL01T-MO-MAP-01:STAGE", None, None),
        (
            1,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MAP-01:STAGE",
            "X",
            None,
        ),
        (
            2,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MAP-01:STAGE",
            "A",
            None,
        ),
    ],
)
def test_gb_extract_entities(gb: Builder, index, type, desc, P, M, R):
    entity = gb.entities[P][index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.P == P
    assert entity.M == M
    assert entity.R == R


def test_setup(gb: Builder):
    gb._services_dir = Path(f"example/{gb.beamline.dom}-services/services")
    gb._write_directory = Path("example/data")
    gb.generate_screens()

    with open(f"./{gb._write_directory}/motor.bob") as f:
        expected = f.read()

    with open("./tests/test_files/motor.bob") as f:
        control = f.read()

    assert expected == control
    if Path.exists(Path(f"./{gb._write_directory}/motor.bob")):
        os.remove(f"./{gb._write_directory}/motor.bob")
