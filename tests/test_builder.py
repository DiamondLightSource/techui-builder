import logging
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from techui_builder.builder import _serialise_json_map, json_map  # type: ignore


def test_builder_beamline_attributes(builder):
    short_dom = "t01"
    long_dom = "bl01t"
    desc = "Test Beamline"

    beamline = builder.beamline
    assert beamline.short_dom == short_dom
    assert beamline.long_dom == long_dom
    assert beamline.desc == desc


@pytest.mark.parametrize(
    "index, name, desc, P, R, attribute, file, extras",
    [
        (0, "fshtr", "Fast Shutter", "BL01T-EA-FSHTR-01", None, None, None, None),
        (1, "d1", "Diode 1", "BL01T-DI-PHDGN-01", None, None, "test.bob", None),
        (
            2,
            "motor",
            "Motor Stage",
            "BL01T-MO-MOTOR-01",
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_builder_component_attributes(
    builder, index, name, desc, P, R, attribute, file, extras
):
    component = builder.components[index]
    assert component.name == name
    assert component.desc == desc
    assert component.P == P
    assert component.R == R
    assert component.attribute == attribute
    if file is not None:
        assert component.file == file
    if extras is not None:
        assert component.extras == extras


def test_missing_service(builder, caplog):
    builder._extract_entities = Mock(side_effect=OSError())
    builder._extract_services()
    for log_output in caplog.records:
        assert "No ioc.yaml file for service:" in log_output.message


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


def test_generate_screens(builder_with_setup):
    builder_with_setup.generate_screens()

    with open(f"{builder_with_setup._write_directory}/motor.bob") as f:
        expected = f.read()

    with open("tests/test_files/motor.bob") as f:
        control = f.read()

    assert expected == control
    if Path.exists(Path(f"{builder_with_setup._write_directory}/motor.bob")):
        os.remove(f"{builder_with_setup._write_directory}/motor.bob")


def test_generate_screens_no_entities(builder, caplog):
    builder.entities = []

    # We only wan't to capture CRITICAL output in this test
    with caplog.at_level(logging.CRITICAL):
        with pytest.raises(SystemExit):
            builder.generate_screens()

    for log_output in caplog.records:
        assert "No ioc entities found, has setup() been run?" in log_output.message


def test_generate_screens_extra_p_does_not_exist(builder_with_setup, caplog):
    # We don't want to actually generate a screen
    builder_with_setup._generate_screen = Mock(side_effect=None)

    builder_with_setup.components[2].extras = ["BAD-PV"]

    # We only want to capture the ERROR output in this test
    with caplog.at_level(logging.ERROR):
        builder_with_setup.generate_screens()

    for log_output in caplog.records:
        assert "Extra prefix BAD-PV" in log_output.message


def test_write_json_map_no_synoptic(builder):
    with pytest.raises(FileNotFoundError):
        builder.write_json_map(synoptic=Path("bad-synoptic.bob"))


def test_write_json_map(builder):
    test_map = json_map("test_bob.bob")

    # We don't want cover _generate_json_map in this test
    builder._generate_json_map = Mock(return_value=test_map)

    # We don't want to access the _serialise_json_map function in this test
    with patch("techui_builder.builder._serialise_json_map") as mock_serialise_json_map:
        mock_serialise_json_map.return_value = {"test": "test"}

        builder.write_json_map()

    dest_path = Path("example/t01-services/synoptic/opis/json_map.json")
    assert Path.exists(dest_path)

    if Path.exists(dest_path):
        os.remove(dest_path)


def test_serialise_json_map():
    # Create test json map with child json map
    test_map_child = json_map("test_child_bob.bob")
    test_map = json_map("test_bob.bob")
    test_map.children.append(test_map_child)

    json_ = _serialise_json_map(test_map)  # type: ignore

    assert json_ == {
        "file": "test_bob.bob",
        "children": [{"file": "test_child_bob.bob"}],
    }
