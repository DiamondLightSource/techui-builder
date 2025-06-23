from pathlib import Path
from pprint import PrettyPrinter

from phoebus_guibuilder import BobScreens, Guibuilder

pp = PrettyPrinter()

dom = "BL23B"

bob_file = Path(f"data/{dom}-synoptic-src.bob")

gui = Guibuilder()

bob_screen = BobScreens(bob_file)
bob_screen.read_bob()
bob_screen.autofill_bob(gui)
bob_screen.write_bob(Path(f"{dom}-synoptic.bob"))
