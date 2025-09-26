import os
from pathlib import Path

import pytest

from techui_builder.builder import Builder


@pytest.fixture
def gb():
    path = Path("example/bl01t-services/synoptic/techui.yaml")
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
    "index, name, desc, p, r, attribute, extras",
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
def test_component_attributes(gb: Builder, index, name, desc, p, r, attribute, extras):
    component = gb.components[index]
    assert component.name == name
    assert component.desc == desc
    assert component.P == p
    assert component.R == r
    assert component.attribute == attribute
    if extras is not None:
        assert component.extras == extras


@pytest.mark.parametrize(
    "index, type, desc, p, m, r",
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
def test_gb_extract_entities(gb: Builder, index, type, desc, p, m, r):
    entity = gb.entities[p][index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.P == p
    assert entity.M == m
    assert entity.R == r


def test_setup(gb: Builder):
    gb._services_dir = Path(f"example/{gb.beamline.dom}-services/services")
    gb._write_directory = gb._services_dir.parent.joinpath("synoptic/opis")
    gb.generate_screens()

    with open(f"./{gb._write_directory}/motor.bob") as f:
        expected = f.read()

    with open("./tests/test_files/motor.bob") as f:
        control = f.read()

    assert expected == control
    if Path.exists(Path(f"./{gb._write_directory}/motor.bob")):
        os.remove(f"./{gb._write_directory}/motor.bob")
