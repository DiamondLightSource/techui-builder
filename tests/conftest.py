import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from lxml.etree import Element, SubElement, tostring
from lxml.objectify import fromstring
from phoebusgen import widget as pwidget

from techui_builder.autofill import Autofiller
from techui_builder.builder import Builder
from techui_builder.generate import Generator
from techui_builder.generate_jsonmap import JsonMap, JsonMapGenerator
from techui_builder.models import Component, SupportEntity
from techui_builder.status import GenerateStatusPvs
from techui_builder.validator import Validator


@pytest.fixture
def tmp_t01_services(tmp_path) -> Path:
    # Copy test files to tmp_path so they are visible to the tests
    shutil.copytree(Path(__file__).parent / "t01-services", tmp_path / "t01-services")

    return tmp_path / "t01-services"


@pytest.fixture
def tmp_test_files(tmp_path) -> Path:
    # Copy test files to tmp_path so they are visible to the tests
    shutil.copytree(Path("tests/test_files/"), tmp_path / "test_files")

    return tmp_path / "test_files"


@pytest.fixture
def builder(tmp_t01_services):
    ixx_services = tmp_t01_services
    techui_path = ixx_services / "synoptic/techui.yaml"

    b = Builder(techui_path)
    b._services_dir = ixx_services / "services"
    b._write_directory = ixx_services / "synoptic"
    return b


@pytest.fixture
def techui_support():
    ts = MagicMock()
    ts.support_modules = {
        "pmac.GeoBrick": SupportEntity(prefix="{{ P }}", macros=["P"], screens=[{}]),
        "pmac.autohome": SupportEntity(prefix="{{ P }}", macros=["P"], screens=[{}]),
        "pmac.dls_pmac_asyn_motor": SupportEntity(
            prefix="{{ P }}{{ M }}", macros=["P", "M"], screens=[{}]
        ),
        "ADAravis.aravisCamera": SupportEntity(
            prefix="{{ P }}{{ R }}",
            macros=["P", "R"],
            screens=[
                {"file": "ADAravis/ADAravis_summary.bob", "type": "embedded"},
                {"file": "ADAravis/ADAravis_detail.bob", "type": "related"},
            ],
        ),
        "ADUVC.UVC": SupportEntity(
            prefix="{{ P }}{{ R }}",
            macros=["P", "R"],
            screens=[
                {"file": "ADUVC/ADUVC_summary.bob", "type": "embedded"},
                {"file": "$(IOC)/ADUVC.pvi.bob", "type": "related"},
            ],
        ),
        "detectorPlugins.detectorPlugins": SupportEntity(
            prefix="{{ P }}{{ R }}",
            macros=["P", "R"],
            screens=[
                {
                    "file": "ADAravis/NDPluginStats.pvi.bob",
                    "suffixes": {
                        "R": ":STAT:",
                    },
                    "type": "related",
                },
                {
                    "file": "ADAravis/NDPluginPva.pvi.bob",
                    "suffixes": {
                        "R": ":PVA:",
                    },
                    "type": "related",
                },
                {
                    "file": "ADAravis/NDPluginROIStat.pvi.bob",
                    "suffixes": {
                        "R": ":ROISTAT:",
                    },
                    "type": "related",
                },
                {
                    "file": "ADAravis/NDFileHDF5.pvi.bob",
                    "suffixes": {
                        "R": ":HDF5:",
                    },
                    "type": "related",
                },
            ],
        ),
        "fastcs.TemperatureController": SupportEntity(
            prefix="{{ name }}", macros=["name"], screens=[{}]
        ),
    }

    return ts


@pytest.fixture
def builder_with_setup(builder: Builder, techui_support):
    with patch("techui_builder.builder.Generator") as mock_generator:
        mock_generator.return_value = MagicMock()

        builder._read_map = Mock()
        builder.techui_support = techui_support

        builder.setup()
        return builder


@pytest.fixture
def builder_with_test_files(builder: Builder, tmp_test_files):
    builder._write_directory = tmp_test_files

    return builder


@pytest.fixture
def components(builder_with_test_files: Builder):
    return builder_with_test_files.conf.components


@pytest.fixture
def json_map_generator(tmp_t01_services):
    return JsonMapGenerator(
        tmp_t01_services / "synoptic/index.bob",
        tmp_t01_services / "synoptic/techui.yaml",
        output=tmp_t01_services / "synoptic",
    )


@pytest.fixture
def status_gen(tmp_t01_services):
    return GenerateStatusPvs(
        tmp_t01_services / "synoptic/techui.yaml",
        output=tmp_t01_services / "synoptic/",
    )


@pytest.fixture
def test_files(tmp_test_files):
    screen_path = tmp_test_files / "test_bob.bob"
    dest_path = tmp_test_files

    return screen_path, dest_path


@pytest.fixture
def example_json_map_root():
    test_map_base = JsonMap("test_bob.bob", "Display")

    return test_map_base


@pytest.fixture
def json_map_generator_with_test_files(tmp_t01_services, tmp_test_files):
    return JsonMapGenerator(
        bob_path=tmp_test_files / "test_bob.bob",
        techui=tmp_t01_services / "synoptic/techui.yaml",
        output=tmp_test_files,
    )


@pytest.fixture
def example_json_map(example_json_map_root):
    # Create test json map with child json map
    test_map_child = JsonMap("test_child_bob.bob", "Detector", exists=False)

    example_json_map_root.children.append(test_map_child)

    return example_json_map_root


@pytest.fixture
def example_display_names_json():
    # Create test json map with correct display names
    test_map_det1 = JsonMap(
        "test_child_bob.bob",
        "Detector (PV-DET-01)",
        macros={"P": "PV-DET-01"},
        exists=False,
    )
    test_map_det2 = JsonMap(
        "test_child_bob.bob",
        "Detector (PV-DET-02)",
        macros={"P": "PV-DET-02"},
        exists=False,
    )
    test_map_det3 = JsonMap(
        "test_child_bob.bob",
        "Detector (PV-DET-03)",
        macros={"P": "PV-DET-03"},
        exists=False,
    )
    test_map_det4 = JsonMap(
        "test_child_bob.bob",
        "Detector (NO PV NAME 1)",
        macros={"R": "NON-P-MACRO"},
        exists=False,
    )
    test_map_dev1 = JsonMap(
        "test_child_bob.bob",
        "Device (PV-DEV-01)",
        macros={"P": "PV-DEV-01"},
        exists=False,
    )
    test_map_dev2 = JsonMap(
        "test_child_bob.bob",
        "Device (PV-DEV-02)",
        macros={"P": "PV-DEV-02"},
        exists=False,
    )
    test_map = JsonMap("test_bob.bob", "Beamline")

    test_map_dev1.children.append(test_map_det1)
    test_map_dev1.children.append(test_map_det2)
    test_map_dev2.children.append(test_map_det3)
    test_map_dev2.children.append(test_map_det4)
    test_map.children.append(test_map_dev1)
    test_map.children.append(test_map_dev2)

    return test_map


@pytest.fixture
def example_json_map_pvi_screens():
    jsonmap = JsonMap(
        file="motor1.bob",
        display_name="motor1",
        exists=True,
        duplicate=False,
        children=[
            JsonMap(
                file="../bl01t-mo-motor-01/pmacAxis.pvi.bob",
                display_name="X1",
                exists=True,
                duplicate=False,
                children=[],
                macros={
                    "M": ":X",
                    "P": "BL01T-MO-MOTOR-01",
                    "label": "X1",
                    "IOC": "https://t01-opis.diamond.ac.uk/bl01t-mo-motor-01",
                },
                error="",
            ),
            JsonMap(
                file="../bl01t-mo-motor-01/pmacAxis.pvi.bob",
                display_name="A",
                exists=True,
                duplicate=False,
                children=[],
                macros={
                    "M": ":A",
                    "P": "BL01T-MO-MOTOR-01",
                    "label": "A",
                    "IOC": "https://t01-opis.diamond.ac.uk/bl01t-mo-motor-01",
                },
                error="",
            ),
            JsonMap(
                file="techui-support/bob/pmac/pmacController.bob",
                display_name="pmacController",
                exists=True,
                duplicate=False,
                children=[],
                macros={"P": "BL01T-MO-BRICK-01"},
                error="",
            ),
        ],
        macros={},
        error="",
    )

    return jsonmap


@pytest.fixture
def generator(techui_support, tmp_t01_services):
    synoptic_dir = tmp_t01_services / "synoptic"
    techui_support_path = synoptic_dir / "techui-support"

    g = Generator(synoptic_dir, "test_url", techui_support_path, techui_support)

    return g


@pytest.fixture
def autofiller(tmp_t01_services):
    index_bob = tmp_t01_services / "synoptic/index.bob"

    a = Autofiller(index_bob, {"test_widget": MagicMock(spec=Component)})

    return a


@pytest.fixture
def validator(tmp_test_files):
    test_bobs = [tmp_test_files / "motor_edited.bob"]
    v = Validator(test_bobs)

    return v


@pytest.fixture
def example_xml_embedded_widget(tmp_test_files):
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
    file_element.text = str(tmp_test_files / "motor_embed.bob")
    macros_element = SubElement(widget_element, "macros")
    macro_element_1 = SubElement(macros_element, "macro1")
    macro_element_1.text = "test_macro_1"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_xml_embedded_widget_pvi_child(tmp_t01_services):
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
    file_element.text = str(tmp_t01_services / "mock_adaravis_service/ADAravis.pvi.bob")
    macros_element = SubElement(widget_element, "macros")
    macro_element_1 = SubElement(macros_element, "macro1")
    macro_element_1.text = "test_macro_1"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_xml_related_widget_pvi_child(tmp_t01_services):
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
    file_element.text = str(tmp_t01_services / "mock_adaravis_service/ADAravis.pvi.bob")
    desc_element = SubElement(action_element, "description")
    desc_element.text = "placeholder description"
    macros_element = SubElement(action_element, "macros")
    macro_element = SubElement(macros_element, "P")
    macro_element.text = "placeholder P"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_xml_related_widget(tmp_t01_services):
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
    file_element.text = str(
        tmp_t01_services / "synoptic/techui-support/bob/pmac/motor.bob"
    )
    desc_element = SubElement(action_element, "description")
    desc_element.text = "placeholder description"
    macros_element = SubElement(action_element, "macros")
    macro_element = SubElement(macros_element, "P")
    macro_element.text = "placeholder P"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_xml_symbol_widget():
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


@pytest.fixture
def example_xml_navtabs_widget(tmp_test_files):
    # You cannot set a text tag of an ObjectifiedElement,
    # so we need to make an etree.Element and convert it ...

    widget_element = Element("widget")
    widget_element.set("type", "navtabs")
    widget_element.set("version", "2.0.0")
    name_element = SubElement(widget_element, "name")
    name_element.text = "navtab"
    width_element = SubElement(widget_element, "width")
    width_element.text = "205"
    height_element = SubElement(widget_element, "height")
    height_element.text = "120"
    tabs_element = SubElement(widget_element, "tabs")
    tab_element_1 = SubElement(tabs_element, "tab")
    tab_element_2 = SubElement(tabs_element, "tab")

    name_element_1 = SubElement(tab_element_1, "name")
    name_element_1.text = "tab1"
    file_element_1 = SubElement(tab_element_1, "file")
    file_element_1.text = str(tmp_test_files / "motor_embed.bob")
    macros_element_1 = SubElement(tab_element_1, "macros")
    macro_element_1 = SubElement(macros_element_1, "macro1")
    macro_element_1.text = "test_macro_1"

    name_element_2 = SubElement(tab_element_2, "name")
    name_element_2.text = "tab2"
    file_element_2 = SubElement(tab_element_2, "file")
    file_element_2.text = str(tmp_test_files / "motor_embed.bob")
    macros_element_2 = SubElement(tab_element_2, "macros")
    macro_element_2 = SubElement(macros_element_2, "macro2")
    macro_element_2.text = "test_macro_2"

    # ... which requires this horror
    widget_element = fromstring(tostring(widget_element))

    return widget_element


@pytest.fixture
def example_pgen_embedded_widget():
    embedded_widget = pwidget.EmbeddedDisplay(
        "CAM", "techui-support/bob/ADAravis/ADAravis_summary.bob", 0, 0, 860, 450
    )
    embedded_widget.macro("P", "BL01T-DI-IOC-01")
    embedded_widget.macro("R", ":CAM:")
    embedded_widget.macro("label", "CAM")
    embedded_widget.macro("IOC", "test_url/bl01t-di-ioc-01")

    return embedded_widget


@pytest.fixture
def example_pgen_related_widget():
    related_widget = pwidget.ActionButton(
        "BRICK", "BRICK", "", x=0, y=0, width=100, height=40
    )
    related_widget.action_open_display(
        file="techui-support/bob/pmac/pmacController.bob",
        target="tab",
        macros={"P": "BL01T-MO-IOC-01"},
    )
    # For some reason the version of action buttons is 3.0.0?
    related_widget.version("2.0.0")

    return related_widget
