from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

import pytest
from lxml import objectify
from phoebusgen import screen as Screen
from phoebusgen import widget as Widget

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


def test_generator_load_screen(generator):
    entity = Entity(type="test", P="TEST", desc=None, M=None, R=None)
    generator.load_screen("test", [entity])

    assert generator.screen_name == "test"
    assert generator.screen_components == [entity]


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
    widget = Widget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120)

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
    widget = Widget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120)

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


def test_generator_create_widget_keyerror(generator, caplog):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    generator.screen_name = "test"
    component = Entity(
        type="key.notavailable", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )

    result = generator._create_widget(component=component)

    assert result is None
    assert (
        "No available widget for key.notavailable in screen test. Skipping..."
        in caplog.text
    )


def test_generator_create_widget_is_list_of_dicts(generator):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    generator._is_list_of_dicts = Mock(return_value=True)
    generator._allocate_widget = Mock(
        return_value=Widget.EmbeddedDisplay(
            name="X", file="", x=0, y=0, width=205, height=120
        )
    )
    generator.screen_name = "test"
    component = Entity(
        type="ADAravis.aravisCamera", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )
    widget = generator._create_widget(component=component)
    for value in widget:
        assert str(value) == str(
            Widget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120)
        )


def test_generator_create_widget_embedded(generator):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    component = Entity(
        type="ADAravis.aravisCamera", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )

    widget = generator._create_widget(
        component=component,
    )
    control_widget = Path("tests/test_files/widget.xml")
    with open(control_widget) as f:
        xml_content = f.read()

    assert str(widget) == xml_content


def test_generator_initialise_name_suffix_m(generator):
    component = Entity(type="test", P="TEST", desc=None, M="T1", R=None)

    name, suffix, suffix_label = generator._initialise_name_suffix(component)

    assert name == "T1"
    assert suffix == "T1"
    assert suffix_label == "M"


def test_generator_initialise_name_suffix_r(generator):
    component = Entity(type="test", P="TEST", desc=None, M=None, R="T1")

    name, suffix, suffix_label = generator._initialise_name_suffix(component)

    assert name == "T1"
    assert suffix == "T1"
    assert suffix_label == "R"


def test_generator_initialise_name_suffix_none(generator):
    component = Entity(type="test", P="TEST", desc=None, M=None, R=None)

    name, suffix, suffix_label = generator._initialise_name_suffix(component)

    assert name == "test"
    assert suffix == ""
    assert suffix_label is None


def test_generator_is_list_of_dicts(generator):
    list_of_dicts = [{"a": 1}, {"b": 2}]
    assert generator._is_list_of_dicts(list_of_dicts) is True


def test_generator_is_list_of_dicts_not(generator):
    not_list_of_dicts = {"a": 1}
    assert generator._is_list_of_dicts(not_list_of_dicts) is False


def test_generator_allocate_widget(generator):
    generator._initilise_name_suffix = Mock(return_value=("CAM:", "CAM:", "R"))

    scrn_mapping = {
        "file": "ADAravis/ADAravis_summary.bob",
        "prefix": "$(P)$(R)",
        "type": "embedded",
    }
    component = Entity(
        type="ADAravis.aravisCamera", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )
    widget = generator._allocate_widget(scrn_mapping, component)
    control_widget = Path("tests/test_files/widget.xml")

    with open(control_widget) as f:
        xml_content = f.read()

    assert str(widget) == xml_content


def test_generator_create_widget_related(generator):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    component = Entity(
        type="pmac.GeoBrick", P="BL23B-MO-BRICK-01", desc=None, M=":M", R=None
    )

    widget = generator._create_widget(
        component=component,
    )

    control_widget = Path("tests/test_files/widget_related.xml")

    with open(control_widget) as f:
        xml_content = f.read()
    assert str(widget) == xml_content


def test_generator_create_widget_related_no_suffix(generator):
    generator._get_screen_dimensions = Mock(return_value=(800, 1280))
    component = Entity(
        type="pmac.GeoBrick", P="BL23B-MO-BRICK-01", desc=None, M=None, R=None
    )

    widget = generator._create_widget(
        component=component,
    )

    control_widget = Path("tests/test_files/widget_related_no_suffix.xml")

    with open(control_widget) as f:
        xml_content = f.read()
    assert str(widget) == xml_content


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


def test_generator_build_groups(generator):
    generator._create_widget = Mock(return_value=Mock())
    generator.layout_widgets = Mock(
        return_value=[
            Widget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120),
            Widget.EmbeddedDisplay(
                name="Y", file="", x=0, y=150, width=205, height=120
            ),
        ]
    )
    generator._get_group_dimensions = Mock(return_value=(600, 400))
    generator.screen_name = "test"
    generator.screen_components = [Mock(), Mock(), Mock()]

    generator.build_groups()
    assert objectify.fromstring(str(generator.screen_)).xpath("//widget[@type='group']")


def test_generator_write_screen(generator):
    generator.screen_name = "test"
    generator.screen_ = Screen.Screen("test")
    generator.widgets = [Mock(), Mock()]
    generator.write_screen(Path("tests/test_files/"))
    assert Path("tests/test_files/test.bob").exists()
    Path("tests/test_files/test.bob").unlink()


def test_generator_write_screen_no_widgets(generator, caplog):
    generator.screen_name = "test"
    generator.screen_ = Screen.Screen("test")
    generator.widgets = []
    generator.write_screen(Path("tests/test_files/"))
    assert "Could not write screen: test as no widgets were available" in caplog.text
