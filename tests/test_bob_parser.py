from unittest.mock import MagicMock

from lxml.etree import _ElementTree

from techui_builder.bob_parser import BobWidget


def test_parse_bob(bob_parser_object, tmp_t01_services):
    test_bob_path = tmp_t01_services / "synoptic/index.bob"
    bob_parser_object._parse_widgets = MagicMock()
    bob_file = bob_parser_object.parse_bob()

    assert bob_file is not None
    assert bob_file.path == test_bob_path
    assert isinstance(bob_file.tree, _ElementTree)
    assert isinstance(bob_file.widgets, list)
    assert isinstance(bob_file.macros, dict)


def test_parse_widgets(bob_parser_object, example_xml_symbol_widget_bob_parser):
    widget = bob_parser_object._parse_widgets(example_xml_symbol_widget_bob_parser)

    for w in widget:
        assert isinstance(w, BobWidget)
        assert w.name == "new"
        assert w.macros["status"] == ["BL01T-TS-TEST-01"]
