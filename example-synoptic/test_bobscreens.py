from pathlib import Path
from pprint import PrettyPrinter

from phoebus_guibuilder import BobScreens, Guibuilder

pp = PrettyPrinter()

bob_file = Path("data/BL23BSynoptic.bob")

gui = Guibuilder()

bob_screen = BobScreens(bob_file)
bob_screen.read_bob()
bob_screen.autofill_bob(gui)
bob_screen.write_bob()
