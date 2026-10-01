from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from lxml import objectify
from typer.testing import CliRunner

from techui_builder.generate_jsonmap import app, log_level
from techui_builder.jsonmap.nodes import ScreenNode

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
    test_map = ScreenNode(str(tmp_test_files / "test_bob.bob"), None)

    # We don't want to cover generate_json_map in this test
    json_map_generator.generate_json_map = Mock(return_value=test_map)

    # We don't want to access the serialise_node function in this test
    with patch("techui_builder.generate_jsonmap.serialise_node") as mock_serialise_node:
        mock_serialise_node.return_value = {"test": "test"}

        json_map_generator.write_json_map()

    dest_path = json_map_generator._write_directory / "JsonMap.json"

    assert Path.exists(dest_path)


def test_generate_json_map(json_map_generator_with_test_files, example_json_map):
    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )

    assert test_json_map == example_json_map


def test_generate_json_map_embedded_screen(
    json_map_generator_with_test_files, example_json_map, tmp_test_files
):
    json_map_generator_with_test_files.bob_path = (
        tmp_test_files / "test_bob_embedded.bob"
    )

    example_json_map.file = "test_bob_embedded.bob"
    example_json_map.children.append(
        ScreenNode(
            "$(IOC)/pmacAxis.pvi.bob",
            display_name="Z",
            exists=False,
            macros={"M": ":EMBED", "P": "BL01T-MO-MOTOR-01", "label": "EMBED"},
        )
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )
    assert test_json_map == example_json_map


def test_generate_json_map_nav_tabs(
    json_map_generator_with_test_files, example_json_map_root, tmp_test_files
):
    json_map_generator_with_test_files.bob_path = (
        tmp_test_files / "test_bob_navtabs.bob"
    )

    example_json_map_root.file = "test_bob_navtabs.bob"
    example_json_map_root.children.extend(
        [
            ScreenNode(display_name="Tab1", file="tab1.bob", exists=False),
            ScreenNode(display_name="Tab2", file="tab2.bob", exists=False),
        ]
    )

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )

    assert test_json_map == example_json_map_root


def test_generate_json_map_child_file_crawl_pvi_screen(
    json_map_generator, example_json_map_pvi_screens, tmp_t01_services
):
    jsonmap = json_map_generator.generate_json_map(
        screen_path=tmp_t01_services / "synoptic/motor1.bob",
    )

    assert example_json_map_pvi_screens == jsonmap


# We don't want to access the _get_action_group function in this test
@patch("techui_builder.jsonmap.links._get_action_group")
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
    mock_get_action_group.return_value = mock_xml

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )
    assert test_json_map == example_json_map


def test_generate_json_map_xml_parse_error(
    json_map_generator_with_test_files, tmp_test_files
):
    json_map_generator_with_test_files.bob_path = tmp_test_files / "test_bob_bad.bob"

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )

    assert test_json_map.error.startswith("XML parse error:")


@patch("techui_builder.jsonmap.links._get_action_group")
def test_generate_json_map_other_exception(
    mock_get_action_group: MagicMock,
    json_map_generator_with_test_files,
):
    mock_get_action_group.side_effect = Exception("Some exception")

    test_json_map = json_map_generator_with_test_files.generate_json_map(
        json_map_generator_with_test_files.bob_path,
    )

    assert test_json_map.error != ""
