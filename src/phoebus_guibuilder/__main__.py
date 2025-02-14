"""Interface for ``python -m phoebus_guibuilder``."""

from argparse import ArgumentParser
from collections.abc import Sequence

from . import __version__, guibuilder

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

    guibuilder.main(_args.filename)


if __name__ == "__main__":
    main()
