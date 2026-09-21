import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from lxml.etree import ElementTree
from lxml.objectify import Element

from techui_builder.models import Component


# Imported in to autofill from utils, so that needs to be patched
@patch("techui_builder.autofill.read_bob")
def test_autofiller_read_bobs(mock_read_bob: MagicMock, autofiller):
    mock_read_bob.return_value = (Mock(spec=ElementTree), Mock())

    autofiller.read_bobs()

    mock_read_bob.assert_called()


def test_autofiller_autofill_bobs(autofiller):
    autofiller._autofill_from_path = Mock()

    autofiller.autofill_bobs()

    autofiller._autofill_from_path.assert_called_once()


def test_autofiller_autofill_from_path_no_navtabs(autofiller):
    autofiller.replace_content = Mock()

    mock_path = MagicMock(spec=Path)
    mock_widget = Element("widget")
    mock_widget.type = "symbol"
    widgets = {"test_widget": mock_widget}
    mock_index_trees = {mock_path: (MagicMock(), widgets)}

    autofiller.index_trees = mock_index_trees

    autofiller._autofill_from_path(mock_path)

    autofiller.replace_content.assert_called()
    assert mock_widget.find("run_actions_on_mouse_click") == "true"


def test_autofiller_autofill_from_path_with_navtabs(
    autofiller, example_xml_navtabs_widget, caplog
):
    autofiller.replace_content = Mock()

    mock_path = MagicMock(spec=Path)
    mock_widget = example_xml_navtabs_widget
    widgets = {"test_widget": mock_widget}
    mock_index_trees = {mock_path: (MagicMock(), widgets)}

    autofiller.index_trees = mock_index_trees

    with caplog.at_level(logging.DEBUG):
        autofiller._autofill_from_path(mock_path)

    assert any(
        log_output.message.startswith("Navtabs widget found on")
        for log_output in caplog.records
    )

    # The example navtab widget doesn't have any widgets in self.gui_components,
    # so replace_content() doesn't get called
    autofiller.replace_content.assert_not_called()


@patch("techui_builder.autofill.objectify.deannotate")
@patch("techui_builder.autofill.ElementTree")
def test_autofiller_write_bob(
    mock_tree: MagicMock, mock_deannotate: MagicMock, autofiller, tmp_test_files
):
    autofiller._write_bob(tmp_test_files / "test_autofilled_bob.bob", mock_tree)

    mock_deannotate.assert_called_once()
    mock_tree.write.assert_called_once_with(
        tmp_test_files / "test_autofilled_bob.bob",
        pretty_print=True,
        encoding="utf-8",
        xml_declaration=True,
    )


def test_autofiller_write_bobs(autofiller):
    autofiller._write_bob = Mock()
    autofiller.index_trees = {MagicMock(spec=Path): (MagicMock(), MagicMock())}

    autofiller.write_bobs()

    autofiller._write_bob.assert_called_once()


@pytest.mark.parametrize(
    "prefix, description, filename, macros, expected_desc, expected_file",
    [
        ("BL01T-TS-TEST-01", None, None, None, "test_component", "test_component.bob"),
        (
            "BL01T-TS-TEST-02",
            "test_desc",
            "test_file.bob",
            None,
            "test_desc",
            "test_file.bob",
        ),
        (
            "BL01T-TS-TEST-03",
            "test_desc",
            "test_file.bob",
            {"TEST": "TEST3"},
            "test_desc",
            "test_file.bob",
        ),
    ],
)
@patch("techui_builder.autofill._get_action_group")
def test_autofiller_replace_content(
    mock_get: MagicMock,
    autofiller,
    example_xml_related_widget,
    prefix,
    description,
    filename,
    macros,
    expected_desc,
    expected_file,
):
    mock_get.return_value = example_xml_related_widget.actions.action

    # Cannot use a Mock object as need P to be computed
    fake_component = Component(
        prefix=prefix,
        label=description,
        file=filename,
        macros=macros,
    )

    autofiller.replace_content(
        example_xml_related_widget,
        "test_component",
        fake_component,
    )

    assert example_xml_related_widget.pv_name == f"{prefix}:STA"
    assert example_xml_related_widget.actions.action.description.text == expected_desc
    assert example_xml_related_widget.actions.action.file.text == expected_file
    if macros is not None:
        for k, v in macros.items():
            assert example_xml_related_widget.actions.action.macros[k] == macros[k] == v


@patch("techui_builder.autofill._get_action_group")
def test_autofiller_replace_content_no_action_group(
    mock_get: MagicMock, autofiller, caplog: pytest.LogCaptureFixture
):
    # Just to only run the code we want to test
    autofiller.macros = ["desc"]

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
