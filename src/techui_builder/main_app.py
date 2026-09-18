import logging
import re
from pathlib import Path
from typing import Annotated

import typer

from techui_builder._logger import log_level
from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder

logger_ = logging.getLogger(__name__)

_DEFAULT_BOBFILE_RE = re.compile(r"index(?:-(?:\w)*)*\.bob")


app = typer.Typer(context_settings={"allow_interspersed_args": True})


def find_dirs(file_path: Path, beamline: str) -> tuple:
    # Get the relative path to the techui file from working dir
    abs_path = file_path.absolute()
    logger_.debug(f"techui.yaml absolute path: {abs_path}")

    # Get the current working dir
    cwd = Path.cwd()
    logger_.debug(f"Working directory: {cwd}")

    directory = beamline

    # Get the relative path of ixx-services to techui.yaml
    ixx_services_dir = next(
        (
            ixx_services.relative_to(cwd, walk_up=True)
            for parent in abs_path.parents
            for ixx_services in parent.glob(f"{directory}-services")
        ),
        None,
    )

    if ixx_services_dir is None:
        if not beamline.startswith("i"):
            # If not found, try searching for Ixx-services as some
            # J/K beamlines are in Ixx-services dir
            directory = f"i{beamline[1:]}"
            logger_.info(
                f"{beamline}-services not found."
                f" Searching for i{beamline[1:]}-services..."
            )
            # Get the relative path of ixx-services to techui.yaml
            ixx_services_dir = next(
                (
                    ixx_services.relative_to(cwd, walk_up=True)
                    for parent in abs_path.parents
                    for ixx_services in parent.glob(f"{directory}-services")
                ),
                None,
            )

    if ixx_services_dir is None:
        logging.critical(
            f"{beamline}-services not found. Is you file structure correct?"
        )
        exit()
    logger_.debug(f"ixx-services relative path: {ixx_services_dir}")

    # Get the synoptic dir relative to the parent dir
    synoptic_dir = abs_path.parent
    logger_.debug(f"synoptic relative path: {synoptic_dir}")

    return ixx_services_dir, synoptic_dir


def find_index_bobs(
    bob_file: Path | None, synoptic_dir: Path
) -> tuple[Path, list[Path]]:
    if bob_file is None:
        # Search default relative dir to techui filename
        # There should be at least one file, but if not return None
        bob_files = [
            p for p in synoptic_dir.iterdir() if _DEFAULT_BOBFILE_RE.match(p.name)
        ]
        if not bob_files:
            logging.critical(
                f"Source bob file not found in {synoptic_dir}. Does it exist?"
            )
            exit()
    elif bob_file.exists():
        # Search for bob files with similar names
        _SIMILAR_BOBFILE_RE = re.compile(  # noqa: N806
            rf"{bob_file.name.removesuffix('.bob')}(?:-(?:\w)*)*\.bob"
        )
        bob_files = [
            p for p in synoptic_dir.iterdir() if _SIMILAR_BOBFILE_RE.match(p.name)
        ]
        if not bob_files:
            logging.critical(
                f"Source bob file not found in {synoptic_dir}. Does it exist?"
            )
            exit()
    else:
        logging.critical("There was an issue finding source bob files. Do they exist?")
        exit()

    index_bob = (
        bob_file
        if bob_file
        else next(
            (f for f in bob_files if f.name == "index.bob"),
            bob_files[0],
        )
    )
    return index_bob, bob_files


# This is the 'build' behaviour
@app.command("build", help="Run `techui-builder build` for a given techui.yaml")
def main(
    filename: Annotated[Path, typer.Argument(help="The path to techui.yaml")],
    bobfile: Annotated[
        Path | None,
        typer.Argument(
            help="Override for template bob file location. This will be used to find"
            " and other template bob files in the same location with similar names."
        ),
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
    """Function to run when `techui-builder build` is called."""

    gui = Builder(techui=filename)

    ixx_services_dir, synoptic_dir = find_dirs(filename, gui.conf.beamline.domain)

    index_bob_path, bob_files = find_index_bobs(bobfile, synoptic_dir)

    # # Overwrite after initialised to make sure this is picked up
    gui._services_dir = ixx_services_dir / "services"  # noqa: SLF001
    gui._write_directory = synoptic_dir  # noqa: SLF001

    logger_.debug(
        f"""

Builder created for {gui.conf.beamline.domain}.
Services directory: {gui._services_dir}
Write directory: {gui._write_directory}
""",  # noqa: SLF001
    )

    gui.setup()
    gui.create_screens()

    logger_.info(f"Screens generated for {gui.conf.beamline.domain}.")

    autofiller = Autofiller(bob_files, index_bob_path, gui.conf.components)
    autofiller.read_bobs()
    autofiller.autofill_bobs()
    autofiller.write_bobs()

    logger_.info(f"Screens autofilled for {gui.conf.beamline.domain}.")
