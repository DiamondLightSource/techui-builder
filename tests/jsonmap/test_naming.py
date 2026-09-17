from pathlib import Path

from techui_builder.jsonmap.naming import (
    find_techui_label,
    fix_duplicate_names,
    name_or_file_stem,
)
from techui_builder.jsonmap.nodes import ScreenNode


def test_name_or_file_stem_with_name():
    """Test parse display name when <name> tag is present"""
    display_name = name_or_file_stem("<name>", Path("/path/to/filename.pvi.bob"))
    assert display_name == "<name>"


def test_name_or_file_stem_from_filepath():
    """Test parse display name when only filepath is present"""
    display_name = name_or_file_stem(None, Path("/path/to/filename.pvi.bob"))
    assert display_name == "filename"


def test_name_or_file_stem_returns_none():
    """Test parse display ensures JSON displayName will return null otherwise"""
    display_name = name_or_file_stem(None, Path(""))

    assert display_name is None


def test_fix_duplicate_names_recursive(example_display_names_json, tmp_test_files):
    """Test duplicate names are enumerated correctly for all children"""

    test_display_names_json = ScreenNode(str(tmp_test_files / "test_bob.bob"), None)

    test_display_names_json_det1 = ScreenNode(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-01"}, exists=False
    )
    test_display_names_json_det2 = ScreenNode(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-02"}, exists=False
    )
    test_display_names_json_det3 = ScreenNode(
        "test_child_bob.bob", "Detector", macros={"P": "PV-DET-03"}, exists=False
    )
    test_display_names_json_det4 = ScreenNode(
        "test_child_bob.bob", "Detector", macros={"R": "NON-P-MACRO"}, exists=False
    )
    test_display_names_json_dev1 = ScreenNode(
        "test_child_bob.bob", "Device", macros={"P": "PV-DEV-01"}, exists=False
    )
    test_display_names_json_dev2 = ScreenNode(
        "test_child_bob.bob", "Device", macros={"P": "PV-DEV-02"}, exists=False
    )
    test_display_names_json = ScreenNode("test_bob.bob", "Beamline")

    test_display_names_json_dev1.children.append(test_display_names_json_det1)
    test_display_names_json_dev1.children.append(test_display_names_json_det2)
    test_display_names_json_dev2.children.append(test_display_names_json_det3)
    test_display_names_json_dev2.children.append(test_display_names_json_det4)
    test_display_names_json.children.append(test_display_names_json_dev1)
    test_display_names_json.children.append(test_display_names_json_dev2)

    fix_duplicate_names(test_display_names_json)

    assert test_display_names_json == example_display_names_json


def test_find_techui_label(json_map_generator_with_test_files):
    display_name = find_techui_label(
        json_map_generator_with_test_files.techui_yaml.components,
        None,
        "motor1",
    )
    assert display_name == "Motor Stage"


def test_find_techui_label_child_labels(json_map_generator_with_test_files):
    display_name = find_techui_label(
        json_map_generator_with_test_files.techui_yaml.components,
        component_name="motor1",
        name="X",
    )
    assert display_name == "X1"


def test_find_techui_label_child_labels_with_name_already_pregenerated(
    json_map_generator_with_test_files,
):
    display_name = find_techui_label(
        json_map_generator_with_test_files.techui_yaml.components,
        component_name="motor1",
        name="X1",
    )
    assert display_name == "X1"


def test_find_techui_label_with_name_elem_invalid(
    json_map_generator_with_test_files,
):
    display_name = find_techui_label(
        json_map_generator_with_test_files.techui_yaml.components,
        component_name=None,
        name="invalid_name",
    )
    assert display_name is None


def test_find_techui_label_with_current_component_name_invalid(
    json_map_generator_with_test_files,
):
    display_name = find_techui_label(
        json_map_generator_with_test_files.techui_yaml.components,
        component_name="invalid_name",
        name="invalid_name",
    )
    assert display_name is None
