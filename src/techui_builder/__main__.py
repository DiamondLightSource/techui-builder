"""Interface for ``python -m techui_builder``."""

import logging
from pathlib import Path
from typing import Annotated

import coloredlogs
import typer

from techui_builder import __version__
from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    help="""
    A script for building Phoebus GUIs.

    This is the required file structure:\n
\n
    ixx-services\n
    |-- services\n
    |   |-- blxxi-ea-device-01\n
    |   |   `-- config\n
    |   |       `-- ioc.yaml\n
    |   |-- ...\n
    |   `-- blxxi-va-device-01\n
    |       `-- config\n
    |           `-- ioc.yaml\n
    `-- synoptic\n
    .   |-- bob-src\n
    .   |   `-- blxxi-synoptic-src.bob\n
    .   |-- create_gui.yaml\n
    .   `-- data\n
""",
)

default_bobfile = "bob-src/blxxi-synoptic-src.bob"


def version_callback(value: bool):
    if value:
        print(f"techui-builder version: {__version__}")
        raise typer.Exit()


logging_field_styles = coloredlogs.DEFAULT_FIELD_STYLES
logging_field_styles.update({"asctime": {"color": "white", "faint": True}})

logging_level_styles = coloredlogs.DEFAULT_LEVEL_STYLES
logging_level_styles.update({"debug": {"color": "green"}})


def log_level(level: str):
    coloredlogs.install(
        level=level,
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        milliseconds=False,
        field_styles=logging_field_styles,
        level_styles=logging_level_styles,
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
    """Default function called from cmd line tool."""

    LOGGER = logging.getLogger(__name__)

    bob_file = bobfile

    # This next part is assuming the file structure:
    #
    # ixx-services
    # |-- services
    # |   |-- blxxi-ea-device-01
    # |   |   `-- config
    # |   |       `-- ioc.yaml
    # |   |-- ...
    # |   `-- blxxi-va-device-01
    # |       `-- config
    # |           `-- ioc.yaml
    # `-- synoptic
    #     |-- bob-src
    #     |   `-- blxxi-synoptic-src.bob
    #     |-- create_gui.yaml
    #     `-- data
    #

    # Get the current working dir
    cwd = Path.cwd()
    LOGGER.debug(f"CWD: {cwd}")

    # Get the relative path to the create_gui file from working dir
    rel_path = filename.absolute().relative_to(cwd, walk_up=True)
    LOGGER.debug(f"create_gui relative path: {rel_path}")

    # Get the relative path of ixx-services to create_gui.yaml
    ixx_services_dir = next(rel_path.parent.parent.parent.glob("*-services"))
    LOGGER.debug(f"ixx-services relative path: {ixx_services_dir}")

    # Get the synoptic dir relative to the parent dir
    synoptic_dir = ixx_services_dir.joinpath("synoptic")
    LOGGER.debug(f"synoptic relative path: {synoptic_dir}")

    if bob_file is None:
        # Search default relative dir to create_gui filename
        # There will only ever be one file, but if not return None
        bob_file = next(
            synoptic_dir.joinpath("bob-src").glob("*-synoptic-src.bob"), None
        )
        if bob_file is None:
            raise Exception(
                f"{default_bobfile} not found in {synoptic_dir.joinpath('bob-src')}. \
Does it exist?"
            )
    else:
        if not bob_file.exists():
            raise Exception(f"{bob_file} not found. Does it exist?")

    LOGGER.debug(f"bob file: {bob_file}")

    gui = Builder(create_gui=filename)
    dom = gui.beamline.dom

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = ixx_services_dir.joinpath("services")  # noqa: SLF001
    gui._write_directory = rel_path.parent.joinpath("data")  # noqa: SLF001

    LOGGER.debug(
        f"""

Builder created for {gui.beamline.dom}.
Services directory: {gui._services_dir}
Write directory: {gui._write_directory}
""",  # noqa: SLF001
    )

    gui.setup()
    gui.generate_screens()

    LOGGER.info(f"Screens generated for {gui.beamline.dom}.")

    autofiller = Autofiller(bob_file)
    autofiller.read_bob()
    autofiller.autofill_bob(gui)
    autofiller.write_bob(gui._write_directory.joinpath(f"{dom}-synoptic.bob"))  # noqa: SLF001

    LOGGER.info(f"Screens autofilled for {gui.beamline.dom}.")


if __name__ == "__main__":
    app()
