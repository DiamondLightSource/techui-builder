import pytest

from techui_builder.objects import Beamline, Component


@pytest.fixture
def beamline() -> Beamline:
    return Beamline(dom="BL01T", desc="Test Beamline")


@pytest.fixture
def component() -> Component:
    return Component(name="TESTDEV", prefix="BL01T-EA-TEST-02", desc="Test Device")


# @pytest.mark.parametrize("beamline,expected",[])
def test_beamline_object(beamline: Beamline):
    assert beamline.dom == "BL01T"
    assert beamline.desc == "Test Beamline"


def test_component_object(component: Component):
    assert component.name == "TESTDEV"
    assert component.desc == "Test Device"
    assert component.service_name is None
    assert component.P == "BL01T-EA-TEST-02"
    assert component.R is None
    assert component.attribute is None


def test_component_repr(component: Component):
    assert (
        str(component)
        == "Component(name=TESTDEV, desc=Test Device, \
            prefix=BL01T-EA-TEST-02, suffix=None, filename=TESTDEV.bob)"
    )


def test_component_bad_prefix():
    with pytest.raises(AttributeError):
        Component(name="BL02T-BAD", prefix="Test 2", desc="BAD_PREFIX")


# def test_component_regex():
