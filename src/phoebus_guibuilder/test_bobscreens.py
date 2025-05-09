from pathlib import Path
from pprint import PrettyPrinter

from phoebus_guibuilder import BobScreens, Guibuilder

pp = PrettyPrinter()

a = Path("example-synoptic/data/BL23BSynoptic.bob")


cgui = (
    Path(__file__).absolute().parent.parent.parent / "example-synoptic/create_gui.yaml"
)

gui = Guibuilder(cgui)
# pp.pprint(gui.components)

b = BobScreens(a)
b.read_bob()
bob = b.autofill_bob(gui)
b.write_bob()
# pp.pprint(bob)
