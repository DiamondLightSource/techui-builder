from pathlib import Path
from pprint import PrettyPrinter

from phoebus_guibuilder import BobScreens, Guibuilder

pp = PrettyPrinter()

a = Path("data/BL23BSynoptic.bob")

gui = Guibuilder()

b = BobScreens(a)
b.read_bob()
bob = b.autofill_bob(gui)
b.write_bob()
