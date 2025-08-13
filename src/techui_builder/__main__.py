"""Interface for ``python -m techui_builder``."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

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


def log_level(level: str):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(omit_repeated_times=False, markup=True)],
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
    ixx_services_dir = next(rel_path.parent.parent.parent.glob("*-services"), None)
    if ixx_services_dir is None:
        logging.critical("ixx-services not found. Is you file structure correct?")
        exit()
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
            logging.critical(
                f"Source bob file '{default_bobfile}' not found in \
{rel_path.parent.joinpath('bob-src')}. Does it exist?"
            )
            exit()
    elif not bob_file.exists():
        logging.critical(f"Source bob file '{bob_file}' not found. Does it exist?")
        exit()

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

    dest_bob = gui._write_directory.joinpath(f"{dom}-synoptic.bob")  # noqa: SLF001

    autofiller.write_bob(dest_bob)

    LOGGER.info(f"Screens autofilled for {gui.beamline.dom}.")

    gui.write_json_map(synoptic=dest_bob, dest=gui._write_directory)  # noqa: SLF001
    LOGGER.info(f"Json map generated for {dom}-synoptic.bob")


if __name__ == "__main__":
    app()
