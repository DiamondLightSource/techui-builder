import pytest

from phoebus_guibuilder.guibuilder import Beamline, Component


@pytest.fixture
def beamline() -> Beamline:
    return Beamline("BL01T", "Test Beamline")


@pytest.fixture
def component() -> Component:
    return Component("TESTDEV", "Test Device", "BL01T-EA-TEST-02")


# @pytest.mark.parametrize("beamline,expected",[])
def test_beamline_object(beamline):
    assert beamline.dom == "BL01T"
    assert beamline.desc == "Test Beamline"


def test_component_object(component):
    assert component.name == "TESTDEV"
    assert component.desc == "Test Device"
    assert component.P == "BL01T-EA-TEST-02"
    assert component.R is None
    assert component.attribute is None


def test_component_repr(component):
    assert (
        str(component)
        == "Component(name=TESTDEV, desc=Test Device, \
prefix=BL01T-EA-TEST-02, suffix=None, filename=None)"
    )


def test_component_bad_prefix():
    with pytest.raises(AttributeError):
        Component("BL02T-BAD", "Test 2", "BAD_PREFIX")


# def test_component_regex():
