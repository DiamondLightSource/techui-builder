"""Interface for ``python -m techui_builder``."""

from pathlib import Path
from typing import Annotated

import coloredlogs
import typer

from techui_builder import __version__
from techui_builder.autofill import Autofiller

from .builder import Builder

# __all__ = ["main"]

app = typer.Typer(pretty_exceptions_show_locals=False)

default_bobfile = "bob-src/blxxi-synoptic-src.bob"


def version_callback(value: bool):
    if value:
        print(f"techui-builder version: {__version__}")
        raise typer.Exit()


def log_level(level: str):
    coloredlogs.install(
        level=level,
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        milliseconds=False,
        field_styles={
            "asctime": {"color": "white", "faint": True},
            "hostname": {"color": "magenta"},
            "levelname": {"bold": True, "color": "black"},
            "name": {"color": "blue"},
            "programname": {"color": "cyan"},
            "username": {"color": "yellow"},
        },
    )


# This is the default behaviour when no command provided
@app.callback(invoke_without_command=True)
def main(
    filename: Annotated[Path, typer.Argument(help="The path to create_gui.yaml")],
    bobfile: Annotated[
        Path | None,
        typer.Argument(help="Override for template bob file location."),
    ] = None,
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback)
    ] = None,
    loglevel: Annotated[
        str,
        typer.Option(
            "--log-level",
            help="Set log level to INFO, DEBUG, WARNING, ERROR or CRITICAL",
            case_sensitive=False,
            callback=log_level,
        ),
    ] = "INFO",
) -> None:
    """Argument parser for the CLI."""

    bob_file = bobfile

    parent_dir = filename.parent

    if bob_file is None:
        # Search default relative dir to create_gui filename
        # There will only ever be one file, but if not return None
        bob_file = next(parent_dir.joinpath("bob-src").glob("*-synoptic-src.bob"), None)
        if bob_file is None:
            raise Exception(f"{default_bobfile} not found. Does it exist?")
    else:
        if not bob_file.exists():
            raise Exception(f"{bob_file} not found. Does it exist?")

    gui = Builder(create_gui=filename)

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = parent_dir.joinpath("bl23b-services/services")  # noqa: SLF001
    gui._write_directory = parent_dir.joinpath("data")  # noqa: SLF001

    gui.setup()
    gui.generate_screens()

    autofiller = Autofiller(bob_file)
    autofiller.read_bob()
    autofiller.autofill_bob(gui)
    autofiller.write_bob(gui._write_directory.joinpath("bl23b-synoptic.bob"))  # noqa: SLF001


if __name__ == "__main__":
    app()
