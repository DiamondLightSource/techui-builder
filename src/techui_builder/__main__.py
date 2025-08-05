"""Interface for ``python -m techui_builder``."""

from pathlib import Path
from typing import Annotated

import typer

from techui_builder import __version__
from techui_builder.autofill import Autofiller

from .builder import Builder

# __all__ = ["main"]

app = typer.Typer()

default_bob_file = Path("example-synoptic/bob-src/blxxi-synoptic-src.bob")


def version_callback(value: bool):
    if value:
        print(f"techui-builder version: {__version__}")
        raise typer.Exit()


# This is the default behaviour when no command provided
@app.callback(invoke_without_command=True)
def main(
    filename: Annotated[Path, typer.Argument(help="The path to create_gui.yaml")],
    bobfile: Annotated[
        Path,
        typer.Argument(help="Override for template bob file location."),
    ] = default_bob_file,
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback)
    ] = None,
) -> None:
    """Argument parser for the CLI."""

    bob_file = bobfile

    if bob_file == default_bob_file:
        # There will only ever be one file, but if not return None
        bob_file = next(
            Path("example-synoptic/bob-src").glob("*-synoptic-src.bob"), None
        )
        if bob_file is None:
            raise Exception(f"{default_bob_file} not found. Does it exist?")

    create_gui_file = filename

    gui = Builder(create_gui=create_gui_file)

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = Path("example-synoptic/bl23b-services/services")  # noqa: SLF001
    gui._write_directory = Path("example-synoptic/data")  # noqa: SLF001

    gui.setup()
    gui.generate_screens()

    autofiller = Autofiller(bob_file)
    autofiller.read_bob()
    autofiller.autofill_bob(gui)
    autofiller.write_bob(gui._write_directory.joinpath("bl23b-synoptic.bob"))  # noqa: SLF001


if __name__ == "__main__":
    app()
