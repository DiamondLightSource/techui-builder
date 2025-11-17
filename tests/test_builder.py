import logging
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from lxml import objectify

from techui_builder.builder import (
    _get_action_group,  # type: ignore
    _serialise_json_map,  # type: ignore
    json_map,
)


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
def test_component_attributes(
    builder, index, name, desc, P, R, attribute, file, extras
):
    components = list(builder.conf.components.keys())
    component = builder.conf.components[components[index]]
    assert components[index] == name
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
    # We don't want to access Generator in this test
    builder_with_setup._generate_screen = Mock()
    builder_with_setup.generate_screens()

    builder_with_setup._generate_screen.assert_called()


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

    components = list(builder_with_setup.conf.components.keys())
    builder_with_setup.conf.components[components[2]].extras = ["BAD-PV"]

    # We only want to capture the ERROR output in this test
    with caplog.at_level(logging.ERROR):
        builder_with_setup.generate_screens()

    for log_output in caplog.records:
        assert "Extra prefix BAD-PV" in log_output.message


def test_write_json_map_no_synoptic(builder):
    with pytest.raises(FileNotFoundError):
        builder.write_json_map(synoptic=Path("bad-synoptic.bob"))


def test_write_json_map(builder):
    test_map = json_map(str(Path(__file__).parent.joinpath("test_files/test_bob.bob")))

    # We don't want cover _generate_json_map in this test
    builder._generate_json_map = Mock(return_value=test_map)

    # Make sure opis/ dir exists
    if not Path.exists(builder._write_directory):
        os.mkdir(builder._write_directory)

    # We don't want to access the _serialise_json_map function in this test
    with patch("techui_builder.builder._serialise_json_map") as mock_serialise_json_map:
        mock_serialise_json_map.return_value = {"test": "test"}

        builder.write_json_map(
            synoptic=builder._write_directory.joinpath("index.bob"),
            dest=builder._write_directory,
        )

    dest_path = builder._write_directory.joinpath("json_map.json")
    assert Path.exists(dest_path)

    if Path.exists(dest_path):
        os.remove(dest_path)


def test_generate_json_map(builder, example_json_map):
    screen_path = Path("tests/test_files/test_bob.bob")
    dest_path = Path("tests/test_files/")

    # We don't want to access the _get_action_group function in this test
    with patch("techui_builder.builder._get_action_group") as mock_get_action_group:
        mock_xml = objectify.Element("action")
        mock_xml["file"] = "test_child_bob.bob"
        mock_get_action_group.return_value = mock_xml

        test_json_map = builder._generate_json_map(screen_path, dest_path)

        assert test_json_map == example_json_map


# TODO: write this test
# def test_generate_json_map_embedded_screen(builder, example_json_map):
#     screen_path = Path("tests/test_files/test_bob.bob")
#     dest_path = Path("tests/test_files/")

#     # Set widget type to embedded
#     ...

#     test_json_map = builder._generate_json_map(screen_path, dest_path)

#     assert test_json_map == example_json_map


def test_generate_json_map_get_macros(builder, example_json_map):
    screen_path = Path("tests/test_files/test_bob.bob")
    dest_path = Path("tests/test_files/")

    # Set a custom macro to test against
    example_json_map.children[0].macros = {"macro": "value"}

    # We don't want to access the _get_action_group function in this test
    with patch("techui_builder.builder._get_action_group") as mock_get_action_group:
        mock_xml = objectify.Element("action")
        mock_xml["file"] = "test_child_bob.bob"
        macros = objectify.SubElement(mock_xml, "macros")
        # Set a macro to test
        macros["macro"] = "value"
        mock_get_action_group.return_value = mock_xml

        test_json_map = builder._generate_json_map(screen_path, dest_path)

        assert test_json_map == example_json_map


def test_generate_json_map_visited_node(builder, example_json_map):
    screen_path = Path("tests/test_files/test_bob.bob")
    dest_path = Path("tests/test_files/")

    visited = {screen_path}
    # Clear children as they will never be read
    example_json_map.children = []
    # Need to set this to true too
    example_json_map.duplicate = True

    test_json_map = builder._generate_json_map(screen_path, dest_path, visited)

    assert test_json_map == example_json_map


def test_generate_json_map_xml_parse_error(builder):
    screen_path = Path("tests/test_files/test_bob_bad.bob")
    dest_path = Path("tests/test_files/")

    test_json_map = builder._generate_json_map(screen_path, dest_path)

    assert test_json_map.error.startswith("XML parse error:")


def test_generate_json_map_other_exception(builder):
    screen_path = Path("tests/test_files/test_bob.bob")
    dest_path = Path("tests/test_files/")

    with patch("techui_builder.builder._get_action_group") as mock_get_action_group:
        mock_get_action_group.side_effect = Exception("Some exception")

        test_json_map = builder._generate_json_map(screen_path, dest_path)

        assert test_json_map.error != ""


def test_serialise_json_map(example_json_map):
    json_ = _serialise_json_map(example_json_map)  # type: ignore

    assert json_ == {
        "file": "tests/test_files/test_bob.bob",
        "children": [{"file": "test_child_bob.bob", "exists": False}],
    }


def test_get_action_group():
    test_bob = objectify.parse("tests/test_files/test_bob.bob")

    widget = test_bob.find(".//widget")
    assert widget is not None

    action_group = _get_action_group(widget)
    assert action_group is not None


def test_get_action_group_no_action_elements():
    test_bob = objectify.parse("tests/test_files/test_bob.bob")

    widget = test_bob.find(".//widget")
    assert widget is not None

    # Clear the actions element
    widget.actions = objectify.ObjectifiedElement()

    action_group = _get_action_group(widget)
    assert action_group is None


def test_get_action_group_no_actions_group(caplog):
    # Use a blank xml element
    widget = objectify.ObjectifiedElement()

    with caplog.at_level(logging.ERROR):
        _get_action_group(widget)

    for log_output in caplog.records:
        assert "Actions group not found" in log_output.message
