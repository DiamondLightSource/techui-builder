import logging
from pathlib import Path
from typing import Annotated

import typer

from techui_builder._logger import log_level
from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder
from techui_builder.utils import find_dirs, find_index_bobs

logger_ = logging.getLogger(__name__)


app = typer.Typer(context_settings={"allow_interspersed_args": True})


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

    if bob_files := find_index_bobs(bobfile, synoptic_dir):
        index_bob_path = (
            bobfile
            if bobfile
            else next(
                (f for f in bob_files if f.name == "index.bob"),
                bob_files[0],
            )
        )
    else:
        exit()

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

    autofiller = Autofiller(
        bob_files, index_bob_path, gui.conf.components, gui.entities
    )
    autofiller.read_bobs()
    autofiller.autofill_bobs()
    autofiller.write_bobs()

    logger_.info(f"Screens autofilled for {gui.conf.beamline.domain}.")
