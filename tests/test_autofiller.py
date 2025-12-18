import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from lxml.etree import ElementTree
from lxml.objectify import Element

from techui_builder.models import Component


def test_autofiller_read_bob(autofiller):
    # Imported in to autofill from utils, so that needs to be patched
    with patch("techui_builder.autofill.read_bob") as mock_read_bob:
        mock_read_bob.return_value = (Mock(spec=ElementTree), Mock())

        autofiller.read_bob()

        mock_read_bob.assert_called()


def test_autofiller_autofill_bob(autofiller):
    autofiller.replace_content = Mock()
    # This mess of a Mock represents a basic Builder object with a components dict
    mock_builder = Mock(conf=Mock(components={"test_widget": Mock(spec=Component)}))

    mock_widget = Element("widget")

    autofiller.widgets = {"test_widget": mock_widget}

    autofiller.autofill_bob(mock_builder)

    autofiller.replace_content.assert_called()
    assert mock_widget.find("run_actions_on_mouse_click") == "true"


def test_autofiller_write_bob(autofiller):
    with (
        patch("techui_builder.builder.etree.ElementTree") as mock_tree,
        patch("techui_builder.builder.objectify.deannotate") as mock_deannotate,
    ):
        autofiller.tree = mock_tree

        autofiller.write_bob(Path("tests/test_files/test_autofilled_bob.bob"))

        mock_deannotate.assert_called_once()
        mock_tree.write.assert_called_once_with(
            Path("tests/test_files/test_autofilled_bob.bob"),
            pretty_print=True,
            encoding="utf-8",
            xml_declaration=True,
        )


@pytest.mark.parametrize(
    "prefix, description, filename, expected_desc, expected_file",
    [
        ("TEST_1", None, None, "test_component", "test_component.bob"),
        ("TEST_2", "test_desc", "test_file.bob", "test_desc", "test_file.bob"),
    ],
)
def test_autofiller_replace_content(
    autofiller,
    example_related_widget,
    prefix,
    description,
    filename,
    expected_desc,
    expected_file,
):
    with patch("techui_builder.autofill._get_action_group") as mock_get:
        mock_get.return_value = example_related_widget.actions.action

        mock_component = Mock(
            spec=Component,
            prefix=prefix,
            desc=description,
            file=filename,
        )

        autofiller.replace_content(
            example_related_widget,
            "test_component",
            mock_component,
        )

        assert example_related_widget.pv_name == f"{prefix}:DEVSTA"
        assert example_related_widget.actions.action.description.text == expected_desc
        assert example_related_widget.actions.action.file.text == expected_file


def test_autofiller_replace_content_no_action_group(autofiller, caplog):
    # Just to only run the code we want to test
    autofiller.macros = ["desc"]

    with patch("techui_builder.autofill._get_action_group") as mock_get:
        # Simulate no action group found
        mock_get.return_value = None

        mock_component = Mock(
            spec=Component,
            desc="description",
        )

        with caplog.at_level(logging.DEBUG):
            autofiller.replace_content(None, "", mock_component)

        for log_output in caplog.records:
            assert "Skipping replace_content for" in log_output.message


def test_autofiller_replace_content_unsupported_macro(autofiller):
    autofiller.macros = ["bad_macro"]

    mock_component = Mock(
        spec=Component,
        bad_macro="bad_macro",
    )

    with pytest.raises(ValueError) as e:
        autofiller.replace_content(None, "", mock_component)

        assert e == "The provided macro type is not supported."
