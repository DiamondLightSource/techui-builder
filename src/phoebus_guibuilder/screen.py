import math
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from pprint import PrettyPrinter

import phoebusgen.screen as Screen
import phoebusgen.widget as Widget
from lxml import etree, objectify
from phoebusgen.widget.widgets import Group as grp

from phoebus_guibuilder.datatypes import Entry

# from phoebus_guibuilder.guibuilder import Guibuilder

STACK_GLOBAL = 3

pp = PrettyPrinter()


class TechUIScreens:
    def __init__(self, screen_components: list[Entry], screen: dict):
        def get_screen_dimensions(file: str):
            """
            Parses the bob files for information on the height
            and width of the screen
            """
            tree = ET.parse(file)
            root = tree.getroot()
            height: str | None = root.findall("height")[0].text

            width: str | None = root.findall("width")[0].text

            return (height, width)

        def default_if_none(value: str | None) -> int:
            """
            Defaults to 100 if no value is returned.
            If there's a value, casts to integer.
            """
            if value is None:
                return 100
            return int(value)

        # Create screen object
        self.screen_components = screen_components
        self.screen_ = Screen.Screen(self.screen_components[0].DESC)
        widgets = []
        groups = []

        # group parameters
        group_padding: int = 30
        group_width: int = group_padding
        group_height: int = group_padding

        self.P: str = "P"
        self.M: str = "M"

        no_of_groups = math.ceil(len(self.screen_components) / STACK_GLOBAL)

        for _grps in range(no_of_groups):
            groups.append(grp("empty", 0, 0, 0, 0))

        # order is an enumeration of the components, used to list them,
        # and serves as functionality in the math for formatting.
        for order, ui in enumerate(self.screen_components):
            # if statement below is check if the suffix is
            # missing from the component description. If
            # not missing, use as name of widget, if missing,
            # use type as name.
            if ui.M is not None:
                name = ui.M
            else:
                name = ui.type

            # Get dimensions of screen from TechUI repository
            if screen[ui.type]["type"] == "embedded":
                height, width = get_screen_dimensions(
                    f"./techui-support/bob/{screen[ui.type]['file']}"
                )

                if height or width is not None:
                    # Overwrite the group width to match the width of the
                    # Embedded  displays making their way into the group.
                    # Add height of the group box with padding based off widget size

                    group_width += default_if_none(width) * (order % 3)
                    group_height = group_padding + default_if_none(
                        height
                    )  # TODO: Make guibuilder pick the height from the largest screen

                    # Create a group based off the number of stacks
                    groups[math.floor(order / STACK_GLOBAL)] = grp(
                        name,
                        math.floor(order / STACK_GLOBAL),
                        math.floor(order / STACK_GLOBAL) * group_height,
                        group_width,
                        group_height,
                    )

                    # Create a widget based off the contents of screen
                    # components

                    widgets.append(
                        Widget.EmbeddedDisplay(
                            name,
                            "./techui-support/bob/" + screen[ui.type]["file"],
                            (default_if_none(width) * (order % 3)),
                            0,  # Change depending on the order
                            default_if_none(width),
                            default_if_none(height),
                        )
                    )

                    # If the group box is changed, reset the width
                    for i in range(len(self.screen_components)):
                        if order == STACK_GLOBAL * i:
                            group_width = group_padding

                    # Add macros to the widgets
                    widgets[order].macro(self.P, ui.P)
                    widgets[order].macro(self.M, ui.M)

            if screen[ui.type]["type"] == "related":
                # TODO: Add grouping action for related screens
                widgets.append(
                    Widget.ActionButton(
                        name,
                        name,
                        "{self.P:self.M}",
                        (70 * order),
                        (50 * math.floor(order / STACK_GLOBAL)),
                        60,
                        40,
                    )
                )

                # Add action to action button: to open related display
                widgets[order].action_open_file(
                    f"./techui-support/bob/{screen[ui.type]['file']}"
                )

        # Add widgets to groups
        start_widget = 0
        end_widget = STACK_GLOBAL
        for group in groups:
            group.add_widget(widgets[start_widget:end_widget])
            start_widget += STACK_GLOBAL
            end_widget += STACK_GLOBAL

        self.screen_.add_widget(groups)
        self.screen_.write_screen(self.screen_components[0].DESC + ".bob")


class BobScreens:
    def __init__(self, bob_path: str | Path):
        bob_path = bob_path if isinstance(bob_path, Path) else Path(bob_path)

        assert bob_path.exists(), warnings.warn(
            f"Bob file {bob_path} can't be found. Does it exist?", stacklevel=1
        )

        self.path = bob_path

    def read_bob(self) -> None:
        # with open(self.path) as f:
        #     bob_file = f.read()

        parser = etree.XMLParser()
        self.tree: etree._ElementTree = objectify.parse(self.path, parser)

        self.root = self.tree.getroot()

    def autofill_bob(self, gui):
        comp_names = [comp.name for comp in gui.components]

        for child in self.root:
            assert isinstance(child, etree._Element)  # noqa: SLF001
            if child.tag == "widget" and child.get("type", default=None) == "symbol":
                symbol_name = child.find("name", namespaces=None).text
                if symbol_name in comp_names:
                    # Get first copy of component
                    comp = next(
                        (comp for comp in gui.components if comp.name == symbol_name),
                    )

                    pv_name: str = child.find("pv_name", namespaces=None).text

                    pv_name = pv_name.replace("{prefix}", comp.prefix)

                    child.find("pv_name", namespaces=None).text = pv_name

    def write_bob(self):
        self.tree.write(
            "BL23B.bob",
            pretty_print=True,  # type: ignore
            encoding="utf-8",  # type: ignore
            xml_declaration=True,  # type: ignore
        )
