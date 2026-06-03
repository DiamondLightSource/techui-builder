import logging
from pathlib import Path
from typing import Annotated

import typer

from techui_builder._logger import log_level
from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder

logger_ = logging.getLogger(__name__)

default_bobfile = "index.bob"


app = typer.Typer(context_settings={"allow_interspersed_args": True})


def find_dirs(file_path: Path, beamline: str) -> tuple:
    # Get the relative path to the techui file from working dir
    abs_path = file_path.absolute()
    logger_.debug(f"techui.yaml absolute path: {abs_path}")

    # Get the current working dir
    cwd = Path.cwd()
    logger_.debug(f"Working directory: {cwd}")

    # Get the relative path of ixx-services to techui.yaml
    ixx_services_dir = next(
        (
            ixx_services.relative_to(cwd, walk_up=True)
            for parent in abs_path.parents
            for ixx_services in parent.glob(f"{beamline}-services")
        ),
        None,
    )
    if ixx_services_dir is None:
        logging.critical("ixx-services not found. Is you file structure correct?")
        exit()
    logger_.debug(f"ixx-services relative path: {ixx_services_dir}")

    # Get the synoptic dir relative to the parent dir
    synoptic_dir = ixx_services_dir.joinpath("synoptic")
    logger_.debug(f"synoptic relative path: {synoptic_dir}")

    return ixx_services_dir, synoptic_dir


def find_bob(bob_file: Path | None, synoptic_dir: Path):
    if bob_file is None:
        # Search default relative dir to techui filename
        # There will only ever be one file, but if not return None
        bob_file = next(
            synoptic_dir.glob(default_bobfile),
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

    logger_.debug(f"bob file: {bob_file}")
    return bob_file


# This is the 'build' behaviour
@app.command("build", help="Run techui-builder for a given techui.yaml")
def main(
    filename: Annotated[Path, typer.Argument(help="The path to techui.yaml")],
    bobfile: Annotated[
        Path | None,
        typer.Argument(help="Override for template bob file location."),
    ] = None,
    loglevel: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-l",
            help="Set log level to INFO, DEBUG, WARNING, ERROR or CRITICAL",
            case_sensitive=False,
            callback=log_level,
        ),
    ] = "INFO",
) -> None:
    """Default function called from cmd line tool."""

    gui = Builder(techui=filename)

    ixx_services_dir, synoptic_dir = find_dirs(filename, gui.conf.beamline.location)

    bob_file = find_bob(bobfile, synoptic_dir)

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = ixx_services_dir.joinpath("services")  # noqa: SLF001
    gui._write_directory = synoptic_dir  # noqa: SLF001

    logger_.debug(
        f"""

Builder created for {gui.conf.beamline.location}.
Services directory: {gui._services_dir}
Write directory: {gui._write_directory}
""",  # noqa: SLF001
    )

    gui.setup()
    gui.create_screens()

    logger_.info(f"Screens generated for {gui.conf.beamline.location}.")

    autofiller = Autofiller(bob_file, gui.conf.components)
    autofiller.read_bob()
    autofiller.autofill_bob()

    dest_bob = gui._write_directory.joinpath("index.bob")  # noqa: SLF001

    autofiller.write_bob(dest_bob)

    logger_.info(f"Screens autofilled for {gui.conf.beamline.location}.")
