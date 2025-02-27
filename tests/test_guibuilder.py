from phoebus_guibuilder.guibuilder import Guibuilder


def test_guibuilder():
    gb = Guibuilder("./example/create_gui.yaml")  #
    assert gb.beamline.dom == "bl01t"
    assert gb.beamline.desc == "Test Beamline"
    assert gb.components[0].name == "fshtr"
    assert gb.components[0].desc == "Fast Shutter"
    assert gb.components[0].P == "BL01T-EA-FSHTR-01"
    assert gb.components[0].R is None
    assert gb.components[0].attribute is None


def test_gb_extract_services():
    gb = Guibuilder("./example/create_gui.yaml")
    gb.find_services_folders()
    assert gb.valid_entities[0].type == "pmac.autohome"
    assert gb.valid_entities[0].DESC == "motor"
    assert gb.valid_entities[0].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.valid_entities[0].M is None
    assert gb.valid_entities[0].R is None
    assert gb.valid_entities[1].type == "pmac.dls_pmac_asyn_motor"
    assert gb.valid_entities[1].DESC == "motor"
    assert gb.valid_entities[1].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.valid_entities[1].M == ":X"
    assert gb.valid_entities[1].R is None
    assert gb.valid_entities[2].type == "pmac.dls_pmac_asyn_motor"
    assert gb.valid_entities[2].DESC == "motor"
    assert gb.valid_entities[2].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.valid_entities[2].M == ":A"
    assert gb.valid_entities[1].R is None


def test_gui_map():
    gb = Guibuilder("./example/create_gui.yaml")
    gb.find_services_folders()
    gb.gui_map()
    assert os.path.isfile("./motor.bob")
