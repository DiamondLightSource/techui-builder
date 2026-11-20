import logging
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


def test_parse_widgets(
    bob_parser_object,
    example_xml_display_container,
    example_xml_symbol_widget_bob_parser,
):
    display = example_xml_display_container(example_xml_symbol_widget_bob_parser)
    widget = bob_parser_object._parse_widgets(display)

    for w in widget:
        assert isinstance(w, BobWidget)
        assert w.name is not None
        assert w.macros["label"] == "test"
        assert w.macros["status"] == ["BL01T-TS-TEST-01"]


def test_parse_widgets_no_macro_pairs(
    bob_parser_object, example_xml_display_container, example_xml_symbol_widget, caplog
):
    display = example_xml_display_container(example_xml_symbol_widget)

    with caplog.at_level(logging.DEBUG):
        widget = bob_parser_object._parse_widgets(display)

    assert any(
        "No MacroDict match for" in log_output.message for log_output in caplog.records
    )

    for w in widget:
        assert isinstance(w, BobWidget)
        assert w.name is not None
        assert w.macros == {}
