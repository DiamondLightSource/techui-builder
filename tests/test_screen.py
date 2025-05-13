import os

from phoebus_guibuilder.guibuilder import Guibuilder


def test_gui_map():
    gb = Guibuilder("./example/create_gui.yaml")
    gb.find_services_folders()
    gb.gui_map()
    assert os.path.isfile("./motor.bob")
