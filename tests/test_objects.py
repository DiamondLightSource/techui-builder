import pytest

from techui_builder.models import Beamline, Component


@pytest.fixture
def beamline() -> Beamline:
    return Beamline(dom="bl01t", desc="Test Beamline")


@pytest.fixture
def component() -> Component:
    return Component(prefix="BL01T-EA-TEST-02", desc="Test Device")


# @pytest.mark.parametrize("beamline,expected",[])
def test_beamline_object(beamline: Beamline):
    assert beamline.long_dom == "bl01t"
    assert beamline.desc == "Test Beamline"


def test_component_object(component: Component):
    assert component.desc == "Test Device"
    assert component.extras is None
    assert component.P == "BL01T-EA-TEST-02"
    assert component.R is None
    assert component.attribute is None


def test_component_repr(component: Component):
    assert (
        str(component)
        == "prefix='BL01T-EA-TEST-02' desc='Test Device' extras=None\
 file=None P='BL01T-EA-TEST-02' R=None attribute=None"
    )


def test_component_bad_prefix():
    with pytest.raises(ValueError):
        Component(prefix="Test 2", desc="BAD_PREFIX")
