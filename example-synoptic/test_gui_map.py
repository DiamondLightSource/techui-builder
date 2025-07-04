from pathlib import Path
from pprint import PrettyPrinter

from techui_builder import Builder

pp = PrettyPrinter()

dom = "BL23B"

bob_file = Path(f"example-synoptic/data/{dom}-synoptic-src.bob")

gui = Builder(create_gui_yaml=Path("example-synoptic/create_gui.yaml"))

gui.read_gui_map()
