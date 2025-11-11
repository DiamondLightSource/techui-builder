from pathlib import Path

import pytest
import yaml
from lxml import objectify
from phoebusgen import widget as Widget

from techui_builder.models import Entity


def test_generator_load_screen(generator):
    entity = Entity(type="test", P="TEST", desc=None, M=None, R=None)
    generator.load_screen("test", [entity])

    assert generator.screen_name == "test"
    assert generator.screen_components == [entity]


def test_generator_get_screen_dimensions(generator):
    test_embedded_screen = "tests/test_files/motor_embed.bob"

    x, y = generator._get_screen_dimensions(test_embedded_screen)

    assert x == 120
    assert y == 205


def test_generator_get_widget_dimensions(generator):
    widget = Path("tests/test_files/widget.xml")

    with open(widget) as f:
        xml_content = f.read()

    height, width = generator._get_widget_dimensions(xml_content)
    assert height == 800
    assert width == 1280


def test_generator_get_widget_position(generator):
    widget = Path("tests/test_files/widget.xml")

    with open(widget) as f:
        xml_content = f.read()

    y, x = generator._get_widget_position(xml_content)
    assert x == 0
    assert y == 0


def test_generator_get_group_dimensions(generator):
    group = Path("tests/test_files/widget_list.yaml")

    with open(group) as f:
        widgets_list = yaml.safe_load(f.read())

    height, width = generator._get_group_dimensions(widget_list=widgets_list)
    assert height == 620
    assert width == 255


def test_generator_initialise_name_suffix(generator):
    component = Entity(type="test", P="TEST", desc=None, M="T1", R=None)

    name, suffix, suffix_label = generator._initialise_name_suffix(component)

    assert name == "T1"
    assert suffix == "T1"
    assert suffix_label == "M"


def test_generator_is_list_of_dicts(generator):
    list_of_dicts = [{"a": 1}, {"b": 2}]
    not_list_of_dicts = {"a": 1}

    assert generator._is_list_of_dicts(list_of_dicts) is True
    assert generator._is_list_of_dicts(not_list_of_dicts) is False


def test_generator_allocate_widget(generator):
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


def test_generator_create_widget(generator):
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


@pytest.mark.parametrize(
    "index, x, y",
    [
        (0, 0, 0),
        (1, 0, 150),
        (2, 0, 300),
        (3, 0, 450),
        (4, 120, 450),
        (5, 0, 520),
    ],
)
def test_generator_layout_widgets(generator, index, x, y):
    widgets_list = [
        Widget.EmbeddedDisplay(name="A", file="", x=0, y=0, width=205, height=120),
        Widget.EmbeddedDisplay(name="X", file="", x=0, y=0, width=205, height=120),
        Widget.EmbeddedDisplay(
            name="pmac.autohome", file="", x=0, y=0, width=205, height=120
        ),
        Widget.EmbeddedDisplay(
            name="pmac.GeoBrick", file="", x=0, y=0, width=100, height=40
        ),
        Widget.ActionButton(
            name="pmac.Action1",
            text="test1",
            pv_name="abc",
            x=0,
            y=0,
            width=100,
            height=40,
        ),
        Widget.ActionButton(
            name="pmac.Action2",
            text="test2",
            pv_name="xyz",
            x=0,
            y=0,
            width=100,
            height=40,
        ),
    ]
    arranged_widgets = generator.layout_widgets(widgets_list)
    assert objectify.fromstring(str(arranged_widgets[index])).x == x
    assert objectify.fromstring(str(arranged_widgets[index])).y == y


def test_generator_build_groups(generator):
    entity = Entity(
        type="ADAravis.aravisCamera", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )
    generator.load_screen("test", [entity])
    generator.build_groups()
    print(generator.screen_)
    assert objectify.fromstring(str(generator.screen_)).xpath("//widget[@type='group']")


def test_generator_write_screen(generator):
    entity = Entity(
        type="ADAravis.aravisCamera", P="BL23B-DI-MOD-02", desc=None, M=None, R="CAM:"
    )
    generator.load_screen("test", [entity])
    generator.build_groups()
    generator.write_screen(Path("tests/test_files/"))
    assert Path("tests/test_files/test.bob").exists()
    Path("tests/test_files/test.bob").unlink()
