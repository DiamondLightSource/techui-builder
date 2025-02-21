from phoebus_guibuilder.guibuilder import Guibuilder


def test_guibuilder():
    gb = Guibuilder("./example/create_gui.yaml")
    gb.extract_from_create_gui()
    print(gb.create_gui)
    print("\n")
    print(gb.components)
    print("\n")
    print(gb.beamline)
    print("\n")


def test_gb_extract_services():
    gb = Guibuilder("./example/create_gui.yaml")
    gb.extract_from_create_gui()
    gb.find_services_extract_ioc()
    print(gb.valid_entities)
