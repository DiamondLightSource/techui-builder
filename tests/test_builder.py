import os
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "attr, expected",
    [
        ("short_dom", "t01"),
        ("long_dom", "bl01t"),
        ("desc", "Test Beamline"),
    ],
)
def test_beamline_attributes(builder, attr, expected):
    assert getattr(builder.conf.beamline, attr) == expected


@pytest.mark.parametrize(
    "index, name, desc, P, R, attribute, extras",
    [
        (0, "fshtr", "Fast Shutter", "BL01T-EA-FSHTR-01", None, None, None),
        (
            4,
            "motor",
            "Motor Stage",
            "BL01T-MO-MOTOR-01",
            None,
            None,
            None,
        ),
    ],
)
def test_component_attributes(builder, index, name, desc, P, R, attribute, extras):
    components = list(builder.conf.components.keys())
    component = builder.conf.components[components[index]]
    assert components[index] == name
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
        (0, "pmac.autohome", None, "BL01T-MO-MOTOR-01", None, None),
        (
            1,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MOTOR-01",
            "X",
            None,
        ),
        (
            2,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MOTOR-01",
            "A",
            None,
        ),
    ],
)
def test_gb_extract_entities(builder, index, type, desc, P, M, R):
    builder._extract_entities(
        builder._services_dir.joinpath("bl01t-mo-ioc-01/config/ioc.yaml")
    )
    entity = builder.entities[P][index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.P == P
    assert entity.M == M
    assert entity.R == R


def test_generate_screens(builder):
    builder.setup()
    builder.generate_screens()

    with open(f"{builder._write_directory}/motor.bob") as f:
        expected = f.read()

    with open("tests/test_files/motor.bob") as f:
        control = f.read()

    assert expected == control
    if Path.exists(Path(f"{builder._write_directory}/motor.bob")):
        os.remove(f"{builder._write_directory}/motor.bob")
