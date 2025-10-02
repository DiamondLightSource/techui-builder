from typer.testing import CliRunner

from techui_builder.__main__ import app

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
