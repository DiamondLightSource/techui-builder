import logging
from unittest.mock import MagicMock, patch

import pytest
from lxml import objectify
from lxml.etree import _ElementTree
from lxml.objectify import Element, ObjectifiedElement

from techui_builder.utils import (
    _get_action_group,
    _get_macros,
    _get_nav_tabs,
    get_widgets,
    read_bob,
)


@patch("techui_builder.utils.get_widgets")
def test_read_bob(mock_get_widgets: MagicMock, tmp_test_files):
    mock_get_widgets.return_value = {"test_widget": MagicMock(spec=ObjectifiedElement)}

    tree, widgets = read_bob(tmp_test_files / "index.bob")

    assert isinstance(tree, _ElementTree)
    assert isinstance(widgets["test_widget"], ObjectifiedElement)
    mock_get_widgets.assert_called_once()


def test_get_widgets(example_xml_symbol_widget):
    test_root = Element("root")
    test_root.append(example_xml_symbol_widget)

    widgets = get_widgets(test_root)

    assert "motor" in widgets.keys()


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


def test_get_macros():
    element = objectify.fromstring(
        "<action><macros><P>BL01T-EA-TEST-01</P></macros></action>"
    )

    assert _get_macros(element) == {"P": "BL01T-EA-TEST-01"}
    assert _get_macros(objectify.fromstring("<action/>")) == {}
