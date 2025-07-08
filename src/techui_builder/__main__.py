"""Interface for ``python -m techui_builder``."""

from argparse import ArgumentParser
from collections.abc import Sequence

from . import __version__
from .builder import Builder

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

    gb = Builder(_args.filename)
    gb.setup()


if __name__ == "__main__":
    main()
