import pytest

from techui_builder.models import (
    Beamline,
    Component,
    GuiComponentEntry,
    GuiComponents,
)


@pytest.fixture
def beamline() -> Beamline:
    return Beamline(short_dom="t01", long_dom="bl01t", desc="Test Beamline")


@pytest.fixture
def component() -> Component:
    return Component(prefix="BL01T-EA-TEST-02", desc="Test Device")


@pytest.fixture
def gui_components() -> GuiComponentEntry:
    return GuiComponentEntry(
        file="digitelMpc/digitelMpcIonp.bob", prefix="$(P)", type="embedded"
    )


# @pytest.mark.parametrize("beamline,expected",[])
def test_beamline_object(beamline: Beamline):
    assert beamline.short_dom == "t01"
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


def test_gui_component_entry(gui_components: GuiComponentEntry):
    assert gui_components.file == "digitelMpc/digitelMpcIonp.bob"
    assert gui_components.prefix == "$(P)"
    assert gui_components.type == "embedded"


def test_gui_components_object(gui_components: GuiComponentEntry):
    gc = GuiComponents({"digitelMpc.digitelMpcIonp": [gui_components]})
    entry = gc.root["digitelMpc.digitelMpcIonp"][0]  # type: ignore
    assert entry.file == "digitelMpc/digitelMpcIonp.bob"

    assert entry.prefix == "$(P)"
    assert entry.type == "embedded"
