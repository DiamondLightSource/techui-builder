import math
import xml.etree.ElementTree as ET

import phoebusgen.screen as Screen
import phoebusgen.widget as Widget

from phoebus_guibuilder.datatypes import Entry

STACK_GLOBAL = 3


class TechUIScreens:
    def __init__(self, screen_components: list[Entry], screen: dict):
        def get_screen_dimensions(file: str):
            tree = ET.parse(file)
            root = tree.getroot()
            height: str | None = root.findall("height")[0].text

            width: str | None = root.findall("width")[0].text

            return (height, width)

        def default_if_none(value: str | None) -> int:
            if value is None:
                return 100
            return int(value)

        self.screen_components = screen_components
        self.screen_ = Screen.Screen(self.screen_components[0].DESC)
        widgets = []

        self.P: str = "P"
        self.M: str = "M"

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

            # Do screen math
            if screen[ui.type]["type"] == "embedded":
                height, width = get_screen_dimensions(
                    f"./techui-support/bob/{screen[ui.type]['file']}"
                )
                if height or width is not None:
                    widgets.append(
                        Widget.EmbeddedDisplay(
                            name,
                            "./techui-support/bob/" + screen[ui.type]["file"],
                            (default_if_none(width) * order),
                            (
                                default_if_none(height)
                                * math.floor(order / STACK_GLOBAL)
                            ),  # Change depending on the order
                            default_if_none(width),
                            default_if_none(height),
                        )
                    )
                    widgets[order].macro(self.P, ui.P)
                    widgets[order].macro(self.M, ui.M)

                    self.screen_.add_widget(widgets[order])

            if screen[ui.type]["type"] == "related":
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

                widgets[order].action_open_file(
                    f"./techui-support/bob/{screen[ui.type]['file']}"
                )
                self.screen_.add_widget(widgets[order])

        self.screen_.write_screen(self.screen_components[0].DESC + ".bob")
