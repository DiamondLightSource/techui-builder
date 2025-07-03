from pathlib import Path
from pprint import PrettyPrinter

from techui_builder import BobScreen, Builder

pp = PrettyPrinter()

dom = "BL23B"

bob_file = Path(f"data/{dom}-synoptic-src.bob")

gui = Builder()

bob_screen = BobScreen(bob_file)
bob_screen.read_bob()
bob_screen.autofill_bob(gui)
bob_screen.write_bob(Path(f"{dom}-synoptic.bob"))
