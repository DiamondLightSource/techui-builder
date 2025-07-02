import subprocess
import sys

from techui_builder import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "techui_builder", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
