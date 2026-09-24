from dataclasses import MISSING, fields

from techui_builder.jsonmap.nodes import ScreenNode, field_default, serialise_node


def test_serialise_node(example_json_map):
    json_ = serialise_node(example_json_map)

    assert json_ == {
        "file": "test_bob.bob",
        "children": [
            {"file": "test_child_bob.bob", "displayName": "Detector", "exists": False}
        ],
        "displayName": "Display",
    }


def test_field_default():
    defaults = {f.name: field_default(f) for f in fields(ScreenNode)}

    assert defaults == {
        "file": MISSING,
        "display_name": MISSING,
        "exists": True,
        "children": [],
        "macros": {},
        "error": "",
    }
