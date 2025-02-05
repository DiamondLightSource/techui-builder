import subprocess
import sys

from phoebus_guibuilder import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "phoebus_guibuilder", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
