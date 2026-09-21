"""Typer app and JsonMapGenerator for generating JsonMap.json."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer
import yaml

from techui_builder._logger import Logger
from techui_builder.jsonmap.crawl import CrawlContext, crawl
from techui_builder.jsonmap.fetch import ScreenFetcher
from techui_builder.jsonmap.nodes import ScreenNode, serialise_node
from techui_builder.models import TechUi

logger_ = logging.getLogger(__name__)


def log_level(level: str):
    Logger(level)


app = typer.Typer(
    pretty_exceptions_show_locals=False,
    context_settings={"allow_interspersed_args": True},
    help="""
    Generate a JSON file mapping of phoebus gui screens.

    This is the required file structure:\n
\n
    ixx-services\n
    `-- synoptic\n
    .   |-- techui-support/\n
    |   |   `-- ...\n
    .   |-- techui.yaml\n
    .   `-- index.bob\n
""",
)


@dataclass
class JsonMapGenerator:
    """Helper class containing functions to generate a JsonMap.json file."""

    bob_path: Path = field(default=Path("index.bob"))
    techui: Path = field(default=Path("techui.yaml"))
    output: Path | None = field(default=None)
    fetcher: ScreenFetcher = field(default_factory=ScreenFetcher)

    def __post_init__(self):
        # Determine the directory to write the json map file to.
        # By default, this looks at the location of the bob file, but can
        # be overwritten using the --output flag
        self._write_directory: Path = (
            self.output if self.output is not None else self.bob_path.parent
        )
        self._parent_path: Path = self.bob_path.parent
        # Check if techui is default value and that it doesn't exist
        if (
            self.techui == self.__class__.__dataclass_fields__["techui"].default
            and not self.techui.exists()
        ):
            self.techui = self._parent_path / "techui.yaml"
        try:
            self.techui_yaml: TechUi = TechUi.model_validate(
                yaml.safe_load(self.techui.read_text(encoding="utf-8"))
            )
        except Exception as e:
            logger_.error(f"Error loading techui.yaml: {e}")
            raise

    def generate_json_map(
        self,
        screen_path: Path,
        current_component_name: str | None = None,
        name_elem: str | None = None,
    ) -> ScreenNode:
        """Recursively generate JSON map from .bob file tree"""
        ctx = CrawlContext(
            components=self.techui_yaml.components,
            synoptic_dir=self._parent_path,
            fetcher=self.fetcher,
            component_name=current_component_name,
            screen=screen_path,
        )
        return crawl(screen_path, ctx, link_name=name_elem)

    def write_json_map(
        self,
    ):
        """Crawl the screen tree from bob_path and write it to JsonMap.json."""
        if not self.bob_path.exists():
            raise FileNotFoundError(
                f"Cannot generate json map for {self.bob_path}. Has it been generated?"
            )

        json_map = self.generate_json_map(self.bob_path)
        with open(self._write_directory / "JsonMap.json", "w") as f:
            f.write(
                json.dumps(json_map, indent=4, default=lambda o: serialise_node(o))
                + "\n"
            )


@app.callback(invoke_without_command=True)
def generate_jsonmap(
    bob_path: Annotated[
        Path,
        typer.Argument(help="Top level bobfile to generate json mapping from."),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Alternative output location for generated json map file.",
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
    """Default function called from cmd line tool."""
    if output_path is not None:
        logger_.info(f"Using user provided output location of: {output_path}")
    jg = JsonMapGenerator(bob_path=bob_path, output=output_path)
    jg.write_json_map()
    logger_.info(
        f"Json map generated for {jg.techui_yaml.beamline.location} (from index.bob)"
    )


if __name__ == "__main__":
    app()
