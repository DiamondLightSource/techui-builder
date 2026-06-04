"""Interface for ``python -m techui_builder``."""

import logging
from typing import Annotated

import typer

from techui_builder._logger import log_level
from techui_builder._version import __version__
from techui_builder.generate_jsonmap import app as generate_jsonmap_app
from techui_builder.main_app import app as main_app
from techui_builder.schema_generator import app as schema_app
from techui_builder.status import app as status_app

logger_ = logging.getLogger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    context_settings={"allow_interspersed_args": True},
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
    .   |-- techui-support/\n
    |   |   `-- ...\n
    .   |-- techui.yaml\n
    .   `-- index.bob\n
""",
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        print(f"techui-builder version: {__version__}")
        raise typer.Exit()


@app.callback()
def _(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version of techui-builder and exit",
    ),
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
):
    """Boilerplate callback function to allow for --version CLI option"""
    pass


app.add_typer(main_app)
app.add_typer(schema_app, name="schema")
app.add_typer(generate_jsonmap_app, name="generate-jsonmap")
app.add_typer(status_app, name="status")


if __name__ == "__main__":
    app()
