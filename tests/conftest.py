from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from lxml.etree import Element, SubElement, tostring
from lxml.objectify import fromstring

from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder, JsonMap
from techui_builder.generate import Generator
from techui_builder.validator import Validator


@pytest.fixture
def builder():
    ixx_services = Path(__file__).parent.joinpath(Path("t01-services"))
    techui_path = ixx_services.joinpath("synoptic/techui.yaml")

    b = Builder(techui_path)
    b._services_dir = ixx_services.joinpath("services")
    b._write_directory = ixx_services.joinpath("synoptic")
    return b


@pytest.fixture
def builder_with_setup(builder: Builder):
    with patch("techui_builder.builder.Generator") as mock_generator:
        mock_generator.return_value = MagicMock()

        builder.setup()
        return builder


@pytest.fixture
def builder_with_test_files(builder: Builder):
    builder._write_directory = Path("tests/test_files/").absolute()

    return builder


@pytest.fixture
def test_files():
    screen_path = Path("tests/test_files/test_bob.bob").absolute()
    dest_path = Path("tests/test_files/").absolute()

    return screen_path, dest_path


@pytest.fixture
def example_json_map():
    # Create test json map with child json map
    test_map_child = JsonMap("test_child_bob.bob", exists=False)
    test_map = JsonMap("test_bob.bob")
    test_map.children.append(test_map_child)

    return test_map


@pytest.fixture
def generator():
    synoptic_dir = Path(__file__).parent.joinpath(Path("t01-services/synoptic"))

    g = Generator(synoptic_dir, "test_url")

    return g


@pytest.fixture
def autofiller():
    index_bob = Path(__file__).parent.joinpath(Path("t01-services/synoptic/index.bob"))

    a = Autofiller(index_bob)

    return a


@pytest.fixture
def validator():
    test_bobs = [Path("tests/test_files/motor-edited.bob")]
    v = Validator(test_bobs)

    return v


@pytest.fixture
def example_embedded_widget():
    # You cannot set a text tag of an ObjectifiedElement,
    # so we need to make an etree.Element and convert it ...

    widget_element = Element("widget")
    widget_element.set("type", "embedded")
    widget_element.set("version", "2.0.0")
    name_element = SubElement(widget_element, "name")
    name_element.text = "motor"
    width_element = SubElement(widget_element, "width")
    width_element.text = "205"
    height_element = SubElement(widget_element, "height")
    height_element.text = "120"
    file_element = SubElement(widget_element, "file")
    file_element.text = "tests/test-files/motor_embed.bob"
    macros_element = SubElement(widget_element, "macros")
    macro_element_1 = SubElement(macros_element, "macro1")
    macro_element_1.text = "test_macro_1"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_related_widget():
    # You cannot set a text tag of an ObjectifiedElement,
    # so we need to make an etree.Element and convert it ...

    widget_element = Element("widget")
    widget_element.set("type", "action_button")
    widget_element.set("version", "2.0.0")
    name_element = SubElement(widget_element, "name")
    name_element.text = "motor"
    width_element = SubElement(widget_element, "width")
    width_element.text = "205"
    height_element = SubElement(widget_element, "height")
    height_element.text = "120"

    actions_element = SubElement(widget_element, "actions")
    action_element = SubElement(actions_element, "action")
    action_element.set("type", "open_display")
    file_element = SubElement(action_element, "file")
    file_element.text = (
        "example/t01-services/synoptic/techui-support/bob/pmac/motor.bob"
    )
    desc_element = SubElement(action_element, "description")
    desc_element.text = "placeholder description"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_symbol_widget():
    # You cannot set a text tag of an ObjectifiedElement,
    # so we need to make an etree.Element and convert it ...
    widget_element = Element("widget")
    widget_element.set("type", "symbol")
    widget_element.set("version", "2.0.0")
    name_element = SubElement(widget_element, "name")
    name_element.text = "motor"
    width_element = SubElement(widget_element, "width")
    width_element.text = "205"
    height_element = SubElement(widget_element, "height")
    height_element.text = "120"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element
