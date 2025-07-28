import os
from pathlib import Path

import pytest

from techui_builder.builder import Builder


@pytest.fixture
def gb():
    b = Builder("./example/create_gui.yaml")
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
    "index, name, desc, P, R, attribute, service_name",
    [
        (0, "fshtr", "Fast Shutter", "BL01T-EA-FSHTR-01", None, None, None),
        (
            4,
            "motor",
            "Hexapod Stage",
            "BL01T-MO-MAP-01",
            "STAGE",
            None,
            "bl01t-mo-ioc-01",
        ),
    ],
)
def test_component_attributes(
    gb: Builder, index, name, desc, P, R, attribute, service_name
):
    component = gb.components[index]
    assert component.name == name
    assert component.desc == desc
    assert component.P == P
    assert component.R == R
    assert component.attribute == attribute
    if service_name is not None:
        assert component.service_name == service_name


@pytest.mark.parametrize(
    "index, type, desc, P, M, R",
    [
        (0, "pmac.GeoBrick", "Hexapod Stage", "BL01T-MO-BRICK-01", None, None),
        (1, "pmac.autohome", "Hexapod Stage", "BL01T-MO-MAP-01:STAGE", None, None),
        (
            2,
            "pmac.dls_pmac_asyn_motor",
            "Hexapod Stage",
            "BL01T-MO-MAP-01:STAGE",
            "X",
            None,
        ),
        (
            3,
            "pmac.dls_pmac_asyn_motor",
            "Hexapod Stage",
            "BL01T-MO-MAP-01:STAGE",
            "A",
            None,
        ),
    ],
)
def test_gb_extract_entities(gb: Builder, index, type, desc, P, M, R):
    gb._extract_entities(
        ioc_yaml=f"example/{gb._services_dir}/services/{gb.components[4].service_name}/config/ioc.yaml",
        component=gb.components[4],
    )
    entity = gb.entities[index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.P == P
    assert entity.M == M
    assert entity.R == R


def test_setup(gb: Builder):
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
