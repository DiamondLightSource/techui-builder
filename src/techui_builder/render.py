from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from techui_builder.models import Beamline


@dataclass
class Renderer:
    support_screen_path: Path
    screen_path: Path
    beamline: Beamline

    def __post_init__(self):
        self.env = Environment(loader=FileSystemLoader(self.support_screen_path))

    def load_screen(self):
        self.screen_template = self.env.get_template(self.screen_path.name)

    def render_screen(self):
        rendered_screen = self.screen_template.render(url=self.beamline.url)
