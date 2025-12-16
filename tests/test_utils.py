from pathlib import Path
from unittest.mock import Mock, patch

from lxml.etree import _ElementTree
from lxml.objectify import Element, ObjectifiedElement

from techui_builder.utils import get_widgets, read_bob


def test_read_bob():
    with patch("techui_builder.utils.get_widgets") as mock_get_widgets:
        mock_get_widgets.return_value = {"test_widget": Mock(spec=ObjectifiedElement)}

        tree, widgets = read_bob(Path("tests/test_files/index.bob"))

        assert isinstance(tree, _ElementTree)
        assert isinstance(widgets["test_widget"], ObjectifiedElement)
        mock_get_widgets.assert_called_once()


def test_get_widgets(example_symbol_widget):
    test_root = Element("root")
    test_root.append(example_symbol_widget)

    widgets = get_widgets(test_root)

    assert "motor" in widgets.keys()
