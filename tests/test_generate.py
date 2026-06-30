from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

import pytest
from lxml import objectify
from phoebusgen import screen as pscreen
from phoebusgen import widget as pwidget

from techui_builder.models import Entity


@dataclass
class FakeWidget:
    width: int
    height: int
    _x: int = 0
    _y: int = 0

    def x(self, val: int):
        self._x = val

    def y(self, val: int):
        self._y = val


def test_generator_get_screen_dimensions_good(generator):
    test_embedded_screen = "tests/test_files/motor_embed.bob"
    x, y = generator._get_screen_dimensions(test_embedded_screen)
    assert x == 120
    assert y == 205


def test_generator_get_screen_dimensions_default(generator):
    test_embedded_screen = "tests/test_files/motor_bad.bob"
    x, y = generator._get_screen_dimensions(test_embedded_screen)
    assert x == 100
    assert y == 100


def test_generator_get_widget_dimensions_good(generator):
    widget = pwidget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120)

    height, width = generator._get_widget_dimensions(widget)
    assert height == 120
    assert width == 205


def test_generator_get_widget_dimensions_default(generator):
    widget_bad = Path("tests/test_files/widget_bad.xml")

    with open(widget_bad) as f:
        xml_content_bad = f.read()

    height, width = generator._get_widget_dimensions(xml_content_bad)
    assert height == 100
    assert width == 100


def test_generator_get_widget_dimensions_default_attribute_error(generator):
    widget_bad = Path("tests/test_files/widget_bad_2.xml")

    with open(widget_bad) as f:
        xml_content_bad = f.read()

    height, width = generator._get_widget_dimensions(xml_content_bad)
    assert height == 100
    assert width == 100


def test_generator_get_widget_position(generator):
    widget = pwidget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120)

    y, x = generator._get_widget_position(widget)
    assert x == 0
    assert y == 0


def test_generator_get_widget_position_default(generator):
    widget_bad = Path("tests/test_files/widget_bad.xml")

    with open(widget_bad) as f:
        xml_content_bad = f.read()

    y, x = generator._get_widget_position(xml_content_bad)
    assert x == 100
    assert y == 100


def test_generator_get_widget_position_default_attribute_error(generator):
    widget_bad = Path("tests/test_files/widget_bad_2.xml")

    with open(widget_bad) as f:
        xml_content_bad = f.read()

    y, x = generator._get_widget_position(xml_content_bad)
    assert x == 100
    assert y == 100


def test_generator_get_group_dimensions(generator):
    generator._get_widget_dimensions = Mock(return_value=(120, 250))
    generator._get_widget_position = Mock(return_value=(0, 0))
    height, width = generator._get_group_dimensions([Mock(), Mock(), Mock(), Mock()])
    assert height == 170
    assert width == 300


def test_generator_create_widgets_keyerror(generator, caplog):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    screen_name = "test"
    component = Entity(
        service_name="bl01t-di-ioc-01",
        type="key.notavailable",
        prefix="BL01T-DI-IOC-01:CAM:",
        desc=None,
        macros={"P": "BL01T-DI-IOC-01", "R": ":CAM:"},
    )

    result = generator._create_widgets(name=screen_name, component=component)

    assert result is None
    assert (
        "No available widget for key.notavailable in screen test. Skipping..."
        in caplog.text
    )


def test_generator_create_widgets_embedded(generator, example_pgen_embedded_widget):
    generator._allocate_widget = Mock(return_value=example_pgen_embedded_widget)

    screen_name = "test"
    component = Entity(
        service_name="bl01t-di-ioc-01",
        type="ADAravis.aravisCamera",
        prefix="BL01T-DI-IOC-01:CAM:",
        desc=None,
        macros={"P": "BL01T-DI-IOC-01", "R": ":CAM:"},
    )

    widget = generator._create_widgets(
        name=screen_name,
        component=component,
    )
    control_widget = Path("tests/test_files/widget.xml")
    with open(control_widget) as f:
        xml_content = f.read()

    # TODO: Do we also need to test the second element
    # that appears to be an action button?
    assert str(widget[0]) == xml_content


def test_generator_update_macros(generator):
    suffix_key = "M"
    suffix = ":T1"

    component = Entity(
        service_name="bl01t-mo-ioc-01",
        type="test",
        prefix="TEST:T1",
        desc=None,
        macros={"P": "TEST", suffix_key: suffix},
    )

    component_name, updated_macros = generator._update_macros(component)

    assert component_name == "T1"
    assert updated_macros[suffix_key] == suffix
    assert updated_macros["label"] == "T1"


def test_generator_update_macros_no_suffix(generator):
    component = Entity(
        service_name="bl01t-ea-ioc-01",
        type="test",
        prefix="TEST",
        desc=None,
        macros={"pv": "TEST"},
    )

    component_name, updated_macros = generator._update_macros(component)

    assert component_name == "test"
    assert len(updated_macros) == 1
    assert updated_macros["pv"] == "TEST"
    assert "label" not in updated_macros.keys()


def test_generator_update_macros_suffix_with_child_labels(generator):
    suffix_key = "R"
    suffix = ":T1"
    child_label = "Test 1"

    component = Entity(
        type="test",
        prefix="TEST:T1",
        desc=None,
        service_name="bl01t-mo-test-01",
        macros={"P": "TEST", suffix_key: suffix},
        child_labels={"T1": child_label},
    )

    component_name, updated_macros = generator._update_macros(component)

    assert component_name == child_label
    assert updated_macros["label"] == child_label


def test_generator_allocate_widget(generator):
    generator._update_macros = Mock(
        return_value=("CAM", {"P": "BL01T-DI-IOC-01", "R": ":CAM:", "label": "CAM"})
    )
    generator._get_screen_dimensions = Mock(return_value=(450, 860))

    scrn_mappings = generator.techui_support.support_modules[
        "ADAravis.aravisCamera"
    ].screens
    scrn_mapping = next((x for x in scrn_mappings if x["type"] == "embedded"), None)

    component = Entity(
        service_name="bl01t-di-ioc-01",
        type="ADAravis.aravisCamera",
        prefix="BL01T-DI-IOC-01:CAM:",
        desc=None,
        macros={"P": "BL01T-DI-IOC-01", "R": ":CAM:"},
    )
    widget = generator._allocate_widget(scrn_mapping, component)
    control_widget = Path("tests/test_files/widget.xml")

    with open(control_widget) as f:
        xml_content = f.read()

    assert str(widget) == xml_content


def test_generator_allocate_widget_with_remote_screens(generator):
    generator._update_macros = Mock(
        return_value=("CAM", {"P": "BL01T-DI-IOC-01", "R": ":CAM:", "label": "CAM"})
    )

    scrn_mappings = generator.techui_support.support_modules["ADUVC.UVC"].screens
    scrn_mapping = next((x for x in scrn_mappings if x["type"] == "related"), None)

    component = Entity(
        service_name="bl01t-di-ioc-01",
        type="ADUVC.UVC",
        prefix="BL01T-DI-IOC-01:CAM:",
        desc=None,
        macros={"P": "BL01T-DI-IOC-01", "R": ":CAM:"},
    )
    widget = generator._allocate_widget(scrn_mapping, component)
    control_widget = Path("tests/test_files/widget_url_screen.xml")

    with open(control_widget) as f:
        xml_content = f.read()
    print(str(widget))
    assert str(widget) == xml_content


def test_generator_allocate_widget_with_custom_suffix(generator):
    generator._update_macros = Mock(return_value=("CAM", {"P": "BL01T-DI-IOC-01"}))
    generator._get_screen_dimensions = Mock(return_value=(40, 100))

    scrn_mappings = generator.techui_support.support_modules[
        "detectorPlugins.detectorPlugins"
    ].screens
    scrn_mapping = next((x for x in scrn_mappings if x["type"] == "related"), None)

    component = Entity(
        service_name="bl01t-di-ioc-01",
        type="detectorPlugins.detectorPlugins",
        prefix="BL01T-DI-IOC-01",
        desc=None,
        macros={"P": "BL01T-DI-IOC-01"},
    )
    widget = generator._allocate_widget(scrn_mapping, component)
    control_widget = Path("tests/test_files/widget_custom_suffix.xml")

    with open(control_widget) as f:
        xml_content = f.read()

    assert str(widget) == xml_content


def test_generator_create_widgets_related(generator, example_pgen_related_widget):
    generator._allocate_widget = Mock(return_value=example_pgen_related_widget)
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))

    component = Entity(
        service_name="bl01t-mo-ioc-01",
        type="pmac.GeoBrick",
        prefix="BL01T-MO-IOC-01",
        desc=None,
        macros={"P": "BL01T-MO-IOC-01"},
    )

    widgets = generator._create_widgets(
        name="BRICK",
        component=component,
    )

    control_widget = Path("tests/test_files/widget_related.xml")
    with open(control_widget) as f:
        xml_content = f.read()
    assert str(widgets[0]) == xml_content


# def test_generator_create_widgets_related_no_suffix(
#     generator, example_pgen_related_widget
# ):
#     generator._allocate_widget = Mock(return_value=example_pgen_related_widget)
#     generator._get_screen_dimensions = Mock(return_value=(800, 1280))

#     component = Entity(
#         service_name="bl01t-mo-ioc-01",
#         type="pmac.GeoBrick",
#         prefix="BL01T-MO-IOC-01",
#         desc=None,
#         macros={"P": "BL01T-MO-IOC-01"},
#     )

#     widgets = generator._create_widgets(
#         name="BRICK",
#         component=component,
#     )

#     control_widget = Path("tests/test_files/widget_related_no_suffix.xml")

#     with open(control_widget) as f:
#         xml_content = f.read()
#     assert str(widgets[0]) == xml_content


@pytest.mark.parametrize(
    "index, x, y",
    [
        (0, 0, 0),
        (1, 0, 150),
        (2, 0, 300),
        (3, 0, 450),
        (4, 0, 600),
        (5, 235, 0),
        (6, 235, 150),
        (7, 355, 150),
        (8, 235, 220),
    ],
)
def test_generator_layout_widgets(generator, index, x, y):
    generator._get_widget_dimensions = Mock(
        side_effect=(lambda fakewidget: (fakewidget.height, fakewidget.width))
    )
    generator._get_widget_position = Mock(
        side_effect=(lambda fakewidget: (fakewidget._y, fakewidget._x))
    )
    widgets_list = [
        FakeWidget(205, 120),
        FakeWidget(205, 120),
        FakeWidget(205, 120),
        FakeWidget(205, 120),
        FakeWidget(205, 120),
        FakeWidget(205, 120),
        FakeWidget(100, 40),
        FakeWidget(100, 40),
        FakeWidget(100, 40),
    ]

    arranged_widgets = generator.layout_widgets(widgets_list)
    assert arranged_widgets[index]._x == x
    assert arranged_widgets[index]._y == y


# TODO: Split up test
def test_generator_build_screen(generator, components):
    generator._create_widgets = Mock(return_value=[Mock()])
    generator.layout_widgets = Mock(
        return_value=[
            pwidget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120),
            pwidget.EmbeddedDisplay(
                name="Y", file="", x=0, y=150, width=205, height=120
            ),
        ]
    )
    generator._get_group_dimensions = Mock(return_value=(600, 400))
    screen_name = "test"
    screen_components = [Mock(), Mock(), Mock()]

    generator.build_widgets(screen_name, screen_components)
    generator.build_groups(screen_name, components)
    generator.build_screen(screen_name)
    assert objectify.fromstring(str(generator.screen_)).xpath("//widget[@type='group']")


def test_build_groups_with_label(generator, components):
    screen_name = "motor"
    generator.widgets = [Mock(), Mock(), Mock()]
    generator._create_widgets = Mock(return_value=Mock())
    generator.layout_widgets = Mock(
        return_value=[
            pwidget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120),
            pwidget.EmbeddedDisplay(
                name="Y", file="", x=0, y=150, width=205, height=120
            ),
        ]
    )
    generator._get_group_dimensions = Mock(return_value=(600, 400))

    generator.build_groups(screen_name, components)
    xml = objectify.fromstring(str(generator.group))
    assert xml.xpath("//name")[0] == "Motor Stage"


def test_build_groups(generator, components):
    screen_name = "test"
    generator.widgets = [Mock(), Mock(), Mock()]
    generator._create_widgets = Mock(return_value=Mock())
    generator.layout_widgets = Mock(
        return_value=[
            pwidget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120),
            pwidget.EmbeddedDisplay(
                name="Y", file="", x=0, y=150, width=205, height=120
            ),
        ]
    )
    generator._get_group_dimensions = Mock(return_value=(600, 400))

    generator.build_groups(screen_name, components)
    xml = objectify.fromstring(str(generator.group))
    assert xml.xpath("//name")[0] == "test"


def test_generator_write_screen(generator):
    screen_name = "test"
    generator.screen_ = pscreen.Screen("test")
    generator.widgets = [Mock(), Mock()]
    generator.write_screen(screen_name, Path("tests/test_files/"))
    assert Path("tests/test_files/test.bob").exists()
    Path("tests/test_files/test.bob").unlink()


def test_generator_write_screen_no_widgets(generator, caplog):
    screen_name = "test"
    generator.screen_ = pscreen.Screen("test")
    generator.widgets = []
    generator.write_screen(screen_name, Path("tests/test_files/"))
    assert "Could not write screen: test as no widgets were available" in caplog.text
