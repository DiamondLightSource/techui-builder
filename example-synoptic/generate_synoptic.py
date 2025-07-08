from pathlib import Path
from pprint import PrettyPrinter

from techui_builder import Builder
from techui_builder.autofill import Autofiller

pp = PrettyPrinter()

# Currently doesn't check for this to be consistent formatting, e.g. .lower()
dom = "bl23b"

bob_file = Path(f"example-synoptic/data/{dom}-synoptic-src.bob")
create_gui_file = Path("example-synoptic/create_gui.yaml")

gui = Builder(create_gui=create_gui_file)

gui.setup()

# TODO: figure out the in-between steps

autofiller = Autofiller(bob_file)
autofiller.read_bob()
autofiller.autofill_bob(gui)
autofiller.write_bob(Path(f"example-synoptic/{dom}-synoptic.bob"))
