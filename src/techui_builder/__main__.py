"""Interface for ``python -m techui_builder``."""

import logging

import typer

from techui_builder.main_app import app as main_app
from techui_builder.schema_generator import app as schema_app
from techui_builder.version import app as version_app

logger_ = logging.getLogger(__name__)

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
    .   |-- techui-support/\n
    |   |   `-- ...\n
    .   |-- techui.yaml\n
    .   `-- index.bob\n
""",
)


app.add_typer(main_app)
app.add_typer(version_app, name="version")
app.add_typer(schema_app, name="schema")


if __name__ == "__main__":
    app()
