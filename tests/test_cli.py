import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from techui_builder.__main__ import (
    app,
    default_bobfile,
    find_bob,
    find_dirs,
    log_level,
    schema_callback,
)

runner = CliRunner()


# def test_app():
#     result = runner.invoke(app, ["example/t01-services/synoptic/techui.yaml"])
#     with patch("techui_builder.builder")
#     assert result.exit_code == 0


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "techui-builder version:" in result.output


# def test_app_log_level():
#     result = runner.invoke(app, ["--log-level", "INFO"])
#     assert result.exit_code == 0


@patch("techui_builder.__main__.schema_generator")
def test_schema_callback(mock_schema_generator):
    with pytest.raises(typer.Exit):
        schema_callback(True)


@patch("techui_builder.__main__.Logger")
def test_log_level(mock_logger):
    log_level("INFO")
    mock_logger.assert_called_once()


def test_find_dirs(caplog):
    mock_services = MagicMock(spec=Path)
    mock_services.relative_to.return_value = Path("mock_rel_path")
    mock_parent = MagicMock(spec=Path)
    mock_parent.glob.return_value = [mock_services]
    mock_absolute = MagicMock()
    mock_absolute.parents = [mock_parent]
    mock_path = MagicMock(spec=Path)
    mock_path.absolute.return_value = mock_absolute

    services, synoptic = find_dirs(mock_path, "ixx")

    assert synoptic == Path("mock_rel_path/synoptic")


def test_find_dirs_no_ixx_services_dir(caplog):
    test_file = MagicMock(spec=Path)
    test_file.parents = []

    with caplog.at_level(logging.CRITICAL) and pytest.raises(SystemExit) as exc_info:
        find_dirs(test_file, "ixx")

    for log_output in caplog.records:
        assert "ixx-services not found." in log_output.message

    # The function calls exit() with no value code
    assert exc_info.value.code is None


def test_find_bob(caplog):
    bob_file = Mock(spec=Path)
    bob_file.exists = MagicMock(return_value=True)

    with caplog.at_level(logging.DEBUG):
        file = find_bob(bob_file, Mock(spec=Path))

    # It should just return back the same file
    assert bob_file == file


def test_find_bob_bob_file_does_not_exist(caplog):
    bad_bob_file = Path("bad_bob_file")
    with caplog.at_level(logging.CRITICAL) and pytest.raises(SystemExit) as exc_info:
        find_bob(bad_bob_file, Mock(spec=Path))

    for log_output in caplog.records:
        assert f"Source bob file '{bad_bob_file}' not found." in log_output.message

    # The function calls exit() with no value code
    assert exc_info.value.code is None


def test_find_bob_no_bob_file_finds_default_bob_file(caplog):
    mock_bob_file = Path("mock_bob_file")
    mock_synoptic_dir = MagicMock(spec=Path)
    mock_synoptic_dir.glob.return_value = iter([mock_bob_file])

    with caplog.at_level(logging.DEBUG):
        _ = find_bob(None, mock_synoptic_dir)

    for log_output in caplog.records:
        assert f"bob file: {mock_bob_file}" in log_output.message


def test_find_bob_no_bob_file_found(caplog):
    mock_synoptic_dir = MagicMock(spec=Path)
    mock_synoptic_dir.glob.return_value = iter([])

    with caplog.at_level(logging.CRITICAL) and pytest.raises(SystemExit) as exc_info:
        _ = find_bob(None, mock_synoptic_dir)

    for log_output in caplog.records:
        assert (
            f"Source bob file '{default_bobfile}' not found in {mock_synoptic_dir}"
            in log_output.message
        )

    # The function calls exit() with no value code
    assert exc_info.value.code is None
