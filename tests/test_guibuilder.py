import os

import pytest

from phoebus_guibuilder.guibuilder import Guibuilder


@pytest.fixture
def gb():
    Guibuilder("./example/create_gui.yaml")
    return Guibuilder("./example/create_gui.yaml")


def test_guibuilder(gb):
    assert gb.beamline.dom == "bl01t"
    assert gb.beamline.desc == "Test Beamline"
    assert gb.components[0].name == "fshtr"
    assert gb.components[0].desc == "Fast Shutter"
    assert gb.components[0].P == "BL01T-EA-FSHTR-01"
    assert gb.components[0].R is None
    assert gb.components[0].attribute is None


def test_gb_extract_services(gb):
    gb.find_services_folders()
    assert gb.entities[0].type == "pmac.autohome"
    assert gb.entities[0].DESC == "motor"
    assert gb.entities[0].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[0].M is None
    assert gb.entities[0].R is None
    assert gb.entities[1].type == "pmac.dls_pmac_asyn_motor"
    assert gb.entities[1].DESC == "motor"
    assert gb.entities[1].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[1].M == "X"
    assert gb.entities[1].R is None
    assert gb.entities[2].type == "pmac.dls_pmac_asyn_motor"
    assert gb.entities[2].DESC == "motor"
    assert gb.entities[2].P == "BL01T-MO-MAP-01:STAGE"
    assert gb.entities[2].M == "A"
    assert gb.entities[1].R is None


def test_gui_map(gb):
    gb.find_services_folders()
    gb.gui_map()
    assert os.path.isfile("./motor.bob")
    assert os.path.isfile("./map.json")
