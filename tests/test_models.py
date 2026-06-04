import pytest

from techui_builder.models import (
    Beamline,
    Component,
    SupportEntity,
)


@pytest.fixture
def beamline() -> Beamline:
    return Beamline(
        location="t01",
        domain="bl01t",
        desc="Test Beamline",
        url="t01-opis.diamond.ac.uk",
    )


@pytest.fixture
def component() -> Component:
    return Component(
        prefix="BL01T-EA-TEST-02",
        label="Test Device",
        status=["BL01T-MO-MOTOR-01:Y"],
        child_labels={"X": "X1", "Y": "Y1", "Z": "Z1"},
    )


@pytest.fixture
def support_entity() -> SupportEntity:
    return SupportEntity(
        prefix="{{ P }}",
        macros=["P"],
        screens=[{"file": "digitelMpc/digitelMpcIonp.bob", "type": "embedded"}],
    )


# @pytest.mark.parametrize("beamline,expected",[])
def test_beamline_object(beamline: Beamline):
    assert beamline.location == "t01"
    assert beamline.domain == "bl01t"
    assert beamline.desc == "Test Beamline"
    assert beamline.url == "https://t01-opis.diamond.ac.uk"


def test_component_object(component: Component):
    assert component.label == "Test Device"
    assert component.extras is None
    assert component.P == "BL01T-EA-TEST-02"
    assert component.R is None
    assert component.attribute is None
    assert component.status == ["BL01T-MO-MOTOR-01:Y"]
    assert component.child_labels == {"X": "X1", "Y": "Y1", "Z": "Z1"}


def test_component_repr(component: Component):
    assert (
        str(component)
        == "prefix='BL01T-EA-TEST-02' label='Test Device' child_labels\
={'X': 'X1', 'Y': 'Y1', 'Z': 'Z1'} extras=None file=None macros=None\
 status=['BL01T-MO-MOTOR-01:Y']"
    )


def test_component_bad_prefix():
    with pytest.raises(ValueError):
        Component(prefix="Test 2", label="BAD_PREFIX")


def test_gui_component_entry(support_entity: SupportEntity):
    assert support_entity.prefix == "{{ P }}"
    assert support_entity.macros == ["P"]
    assert support_entity.screens[0]["file"] == "digitelMpc/digitelMpcIonp.bob"
    assert support_entity.screens[0]["type"] == "embedded"
