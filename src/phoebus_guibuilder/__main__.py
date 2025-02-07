"""Interface for ``python -m phoebus_guibuilder``."""

from argparse import ArgumentParser
from collections.abc import Sequence
from fileinput import filename

from . import __version__
from .guibuilder import Guibuilder

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser()
    parser.add_argument("filename", help="The path to create_gui.yaml")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    _args = parser.parse_args(args)

    gb = Guibuilder(_args.filename)
    gb.extract_from_create_gui()


if __name__ == "__main__":
    main()
