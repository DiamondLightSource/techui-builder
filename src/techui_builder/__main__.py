"""Interface for ``python -m techui_builder``."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from techui_builder import __version__
from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder
from techui_builder.schema_generator import schema_generator

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
    .   |-- techui.yaml\n
    .   `-- opis-src\n
    .       `-- index-src.bob\n
""",
)

default_bobfile = "index-src.bob"


def version_callback(value: bool):
    if value:
        print(f"techui-builder version: {__version__}")
        raise typer.Exit()


def schema_callback(value: bool):
    if value:
        schema_generator()
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
    filename: Annotated[Path, typer.Argument(help="The path to techui.yaml")],
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
    schema: Annotated[
        bool | None,
        typer.Option(
            "--schema",
            help="Generate schema for validating techui and ibek-mapping yaml files",
            callback=schema_callback,
        ),
    ] = None,
) -> None:
    """Default function called from cmd line tool."""

    LOGGER = logging.getLogger(__name__)

    bob_file = bobfile

    gui = Builder(techui=filename)

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
    # .   |-- techui.yaml
    # .   `-- opis-src
    # .       `-- index-src.bob
    #

    # Get the relative path to the techui file from working dir
    abs_path = filename.absolute()
    LOGGER.debug(f"techui.yaml absolute path: {abs_path}")

    # Get the current working dir
    cwd = Path.cwd()
    LOGGER.debug(f"Working directory: {cwd}")

    # Get the relative path of ixx-services to techui.yaml
    ixx_services_dir = next(
        (
            ixx_services.relative_to(cwd, walk_up=True)
            for parent in abs_path.parents
            for ixx_services in parent.glob(f"{gui.conf.beamline.short_dom}-services")
        ),
        None,
    )
    if ixx_services_dir is None:
        logging.critical("ixx-services not found. Is you file structure correct?")
        exit()
    LOGGER.debug(f"ixx-services relative path: {ixx_services_dir}")

    # Get the synoptic dir relative to the parent dir
    synoptic_dir = ixx_services_dir.joinpath("synoptic")
    LOGGER.debug(f"synoptic relative path: {synoptic_dir}")

    if bob_file is None:
        # Search default relative dir to techui filename
        # There will only ever be one file, but if not return None
        bob_file = next(
            synoptic_dir.glob("index.bob"),
            None,
        )
        if bob_file is None:
            logging.critical(
                f"Source bob file '{default_bobfile}' not found in \
{synoptic_dir}. Does it exist?"
            )
            exit()
    elif not bob_file.exists():
        logging.critical(f"Source bob file '{bob_file}' not found. Does it exist?")
        exit()

    LOGGER.debug(f"bob file: {bob_file}")

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = ixx_services_dir.joinpath("services")  # noqa: SLF001
    gui._write_directory = synoptic_dir  # noqa: SLF001

    LOGGER.debug(
        f"""

Builder created for {gui.conf.beamline.short_dom}.
Services directory: {gui._services_dir}
Write directory: {gui._write_directory}
""",  # noqa: SLF001
    )

    gui.setup()
    gui.generate_screens()

    LOGGER.info(f"Screens generated for {gui.conf.beamline.short_dom}.")

    autofiller = Autofiller(bob_file)
    autofiller.read_bob()
    autofiller.autofill_bob(gui)

    dest_bob = gui._write_directory.joinpath("index.bob")  # noqa: SLF001

    autofiller.write_bob(dest_bob)

    LOGGER.info(f"Screens autofilled for {gui.conf.beamline.short_dom}.")

    gui.write_json_map(synoptic=dest_bob, dest=gui._write_directory)  # noqa: SLF001
    LOGGER.info(
        f"Json map generated for {gui.conf.beamline.short_dom} (from index.bob)"
    )


if __name__ == "__main__":
    app()
