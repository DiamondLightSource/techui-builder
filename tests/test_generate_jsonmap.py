import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from lxml import objectify
from typer.testing import CliRunner

from techui_builder.generate_jsonmap import (
    JsonMap,
    _get_action_group,
    _get_nav_tabs,  # type: ignore
    _serialise_json_map,
    app,
    log_level,
)

runner = CliRunner()


@patch("techui_builder.generate_jsonmap.Logger")
def test_log_level(mock_logger: MagicMock):
    log_level("INFO")
    mock_logger.assert_called_once()


def test_write_json_map_no_synoptic(json_map_generator):
    with pytest.raises(FileNotFoundError):
        json_map_generator.bob_path = Path("Synoptic")
        json_map_generator.write_json_map()


def test_app(tmp_t01_services):
    result = runner.invoke(
        app,
        [
            str(tmp_t01_services / "synoptic/index.bob"),
            "--output",
            str(tmp_t01_services / "synoptic"),
        ],
    )

    assert result.exit_code == 0


@patch("techui_builder.generate_jsonmap.yaml.safe_load")
def test_json_map_generator_techui_exception(
    mock_safe_load: MagicMock, json_map_generator, tmp_test_files
):
    mock_safe_load.side_effect = Exception("YAML load error")
    with pytest.raises(Exception) as excinfo:
        json_map_generator.__init__(bob_path=tmp_test_files / "test_bob.bob")

    assert "No such file or directory" in str(excinfo.value)


def test_write_json_map(json_map_generator, tmp_test_files):
    test_map = JsonMap(str(tmp_test_files / "test_bob.bob"), None)

    # We don't want cover _generate_json_map in this test
    json_map_generator.generate_json_map = Mock(return_value=test_map)

    # We don't want to access the _serialise_json_map function in this test
    with patch(
        "techui_builder.generate_jsonmap._serialise_json_map"
    ) as mock_serialise_json_map:
        mock_serialise_json_map.return_value = {"test": "test"}

        json_map_generator.write_json_map()

    dest_path = json_map_generator._write_directory / "JsonMap.json"

    assert Path.exists(dest_path)


# We don't want to access the _get_action_group function in this test
@patch("techui_builder.generate_jsonmap._get_action_group")
def test_generate_json_map(
    mock_get_action_group: MagicMock,
    json_map_generator_with_test_files,
    example_json_map,
):
    mock_xml = objectify.Element("action")
    mock_xml["file"] = "test_child_bob.bob"
    mock_get_action_group.return_value = mock_xml
    json_map_generator_with_test_files._parse_display_name = Mock(
        side_effect=["Display", "Detector"]
    )
    json_map_generator_with_test_files._get_component_label = Mock(
        side_effect=["Display", "Detector"]
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )

    assert test_json_map == example_json_map


def test_generate_json_map_embedded_screen(
    json_map_generator_with_test_files, example_json_map, tmp_test_files
):
    list_names = [
        "Display",
        "Detector",
        "Embedded Display",
        "Embedded Display",
        "Embedded Display",
    ]
    json_map_generator_with_test_files._parse_display_name = Mock(
        side_effect=list_names
    )
    json_map_generator_with_test_files._get_component_label = Mock(
        side_effect=list_names
    )

    json_map_generator_with_test_files.bob_path = (
        tmp_test_files / "test_bob_embedded.bob"
    )

    example_json_map.file = "test_bob_embedded.bob"
    example_json_map.children.append(
        JsonMap(
            "$(IOC)/pmacAxis.pvi.bob",
            display_name="Embedded Display",
            exists=False,
            macros={"M": ":EMBED", "P": "BL01T-MO-MOTOR-01", "label": "EMBED"},
        )
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )
    assert test_json_map == example_json_map


def test_generate_json_map_nav_tabs(
    json_map_generator_with_test_files, example_json_map_root, tmp_test_files
):
    json_map_generator_with_test_files._parse_display_name = Mock(
        side_effect=["Display", "Tab1", "Tab2"]
    )
    json_map_generator_with_test_files._get_component_label = Mock(
        side_effect=["Display", "Tab1", "Tab2"]
    )

    json_map_generator_with_test_files.bob_path = (
        tmp_test_files / "test_bob_navtabs.bob"
    )

    example_json_map_root.file = "test_bob_navtabs.bob"
    example_json_map_root.children.extend(
        [
            JsonMap(display_name="Tab1", file="tab1.bob", exists=False),
            JsonMap(display_name="Tab2", file="tab2.bob", exists=False),
        ]
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )

    assert test_json_map == example_json_map_root


def test_parse_display_name_with_name(json_map_generator):
    """Test parse display name when <name> tag is present"""
    display_name = json_map_generator._parse_display_name(
        "<name>", Path("/path/to/filename.pvi.bob")
    )
    assert display_name == "<name>"


def test_parse_display_name_from_filepath(json_map_generator):
    """Test parse display name when only filepath is present"""
    display_name = json_map_generator._parse_display_name(
        None, Path("/path/to/filename.pvi.bob")
    )
    assert display_name == "filename"


def test_parse_display_name_returns_none(json_map_generator):
    """Test parse display ensures JSON displayName will return null otherwise"""
    display_name = json_map_generator._parse_display_name(None, Path(""))

    assert display_name is None


def test_fix_names_json_map_recursive(
    json_map_generator, example_display_names_json, tmp_test_files
):
    """Test duplicate names are enumerated correctly for all children"""

    test_display_names_json = JsonMap(str(tmp_test_files / "test_bob.bob"), None)

    test_display_names_json_det1 = JsonMap(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-01"}, exists=False
    )
    test_display_names_json_det2 = JsonMap(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-02"}, exists=False
    )
    test_display_names_json_det3 = JsonMap(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-03"}, exists=False
    )
    test_display_names_json_det4 = JsonMap(
        "test_child_bob.bob", "Detector", macros={"R": "NON-P-MACRO"}, exists=False
    )
    test_display_names_json_dev1 = JsonMap(
        "test_child_bob.bob", "Device", macros={"P": "PV-DEV-01"}, exists=False
    )
    test_display_names_json_dev2 = JsonMap(
        "test_child_bob.bob", "Device", macros={"P": "PV-DEV-02"}, exists=False
    )
    test_display_names_json = JsonMap("test_bob.bob", "Beamline")

    test_display_names_json_dev1.children.append(test_display_names_json_det1)
    test_display_names_json_dev1.children.append(test_display_names_json_det2)
    test_display_names_json_dev2.children.append(test_display_names_json_det3)
    test_display_names_json_dev2.children.append(test_display_names_json_det4)
    test_display_names_json.children.append(test_display_names_json_dev1)
    test_display_names_json.children.append(test_display_names_json_dev2)

    json_map_generator._fix_names_json_map(test_display_names_json)

    assert test_display_names_json == example_display_names_json


# We don't want to access the _get_action_group function in this test
@patch("techui_builder.generate_jsonmap._get_action_group")
def test_generate_json_map_get_macros(
    mock_get_action_group: MagicMock,
    json_map_generator_with_test_files,
    example_json_map,
):
    # Set a custom macro to test against
    example_json_map.children[0].macros = {"macro": "value"}

    mock_xml = objectify.Element("action")
    mock_xml["file"] = "test_child_bob.bob"
    macros = objectify.SubElement(mock_xml, "macros")
    # Set a macro to test
    macros["macro"] = "value"
    json_map_generator_with_test_files._parse_display_name = Mock(
        side_effect=["Display", "Detector"]
    )
    json_map_generator_with_test_files._get_component_label = Mock(
        side_effect=["Display", "Detector"]
    )
    mock_get_action_group.return_value = mock_xml

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )
    assert test_json_map == example_json_map


def test_generate_json_map_xml_parse_error(
    json_map_generator_with_test_files, tmp_test_files
):
    json_map_generator_with_test_files.bob_path = tmp_test_files / "test_bob_bad.bob"

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )

    assert test_json_map.error.startswith("XML parse error:")


@patch("techui_builder.generate_jsonmap._get_action_group")
def test_generate_json_map_other_exception(
    mock_get_action_group: MagicMock,
    json_map_generator_with_test_files,
):
    mock_get_action_group.side_effect = Exception("Some exception")
    json_map_generator_with_test_files._parse_display_name = Mock(
        side_effect=["Display", "Detector"]
    )
    json_map_generator_with_test_files._get_component_label = Mock(
        side_effect=["Display", "Detector"]
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
        json_map_generator_with_test_files._write_directory,
    )

    assert test_json_map.error != ""


def test_serialise_json_map(example_json_map):
    json_ = _serialise_json_map(example_json_map)  # type: ignore

    assert json_ == {
        "file": "test_bob.bob",
        "children": [
            {"file": "test_child_bob.bob", "displayName": "Detector", "exists": False}
        ],
        "displayName": "Display",
    }


def test_get_action_group(tmp_test_files):
    test_bob = objectify.parse(tmp_test_files / "test_bob.bob")

    widget = test_bob.find(".//widget")
    assert widget is not None

    action_group = _get_action_group(widget)
    assert action_group is not None


def test_get_action_group_no_action_elements(tmp_test_files):
    test_bob = objectify.parse(tmp_test_files / "test_bob.bob")

    widget = test_bob.find(".//widget")
    assert widget is not None

    # Clear the actions element
    widget.actions = objectify.ObjectifiedElement()

    action_group = _get_action_group(widget)
    assert action_group is None


def test_get_action_group_no_actions_group(caplog: pytest.LogCaptureFixture):
    # Use a blank xml element
    widget = objectify.ObjectifiedElement()
    # TODO: Do widgets always have a name attr, or _can_ it be empty??
    widget.name = "Test"

    with caplog.at_level(logging.ERROR):
        _get_action_group(widget)

    for log_output in caplog.records:
        assert "Actions group not found" in log_output.message


def test_get_component_label(json_map_generator_with_test_files):
    display_name = json_map_generator_with_test_files._get_component_label(
        "motor1",
        None,
        None,
    )
    assert display_name == "Motor Stage"


def test_get_component_label_child_labels(json_map_generator_with_test_files):
    display_name = json_map_generator_with_test_files._get_component_label(
        "X",
        current_component_name="motor1",
        display_name="X",
    )
    assert display_name == "X1"


def test_get_component_label_child_labels_with_name_already_pregenerated(
    json_map_generator_with_test_files,
):
    display_name = json_map_generator_with_test_files._get_component_label(
        "X1",
        current_component_name="motor1",
        display_name="X",
    )
    assert display_name == "X1"


def test_get_component_label_with_name_elem_invalid(
    json_map_generator_with_test_files,
):
    display_name = json_map_generator_with_test_files._get_component_label(
        "invalid_name",
        current_component_name=None,
        display_name="new_name",
    )
    assert display_name == "new_name"


def test_get_component_label_with_current_component_name_invalid(
    json_map_generator_with_test_files,
):
    display_name = json_map_generator_with_test_files._get_component_label(
        "invalid_name",
        current_component_name="invalid_name",
        display_name="new_name",
    )
    assert display_name == "new_name"


def test_get_nav_tabs(example_xml_navtabs_widget):
    tabs_widget = _get_nav_tabs(example_xml_navtabs_widget)

    assert isinstance(tabs_widget, list)


def test_get_nav_tabs_no_tabs_group(caplog: pytest.LogCaptureFixture):
    mock_navtabs = MagicMock(spec=objectify.ObjectifiedElement)
    mock_navtabs.name = "no_tabs"

    with caplog.at_level(logging.ERROR):
        _get_nav_tabs(mock_navtabs)

    for log_output in caplog.records:
        assert "Tabs group not found" in log_output.message
