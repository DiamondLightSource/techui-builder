import phoebusgen.screen as Screen
import phoebusgen.widget as Widget
from lxml import etree  # type: ignore
from phoebusgen.widget.widgets import Group as grp

from techui_builder.datatypes import Entry

STACK_GLOBAL = 3


class TechUIScreens:
    def __init__(self, screen_components: list[Entry], screen: dict):
        self.default_size = 100

        def get_screen_dimensions(file: str) -> tuple[int, int]:
            """
            Parses the bob files for information on the height
            and width of the screen
            """
            tree = etree.parse(file, None)
            root = tree.getroot()
            height_element: etree._Element | None = root.find("height")
            if height_element is not None:
                height = (
                    self.default_size
                    if (val := height_element.text) is None
                    else int(val)
                )
            else:
                height = self.default_size
                # Assert that could not obtaint the sizes of the widget

            width_element: etree._Element | None = root.find("width")
            if width_element is not None:
                width = (
                    self.default_size
                    if (val := width_element.text) is None
                    else int(val)
                )
            else:
                width = self.default_size
                # Assert that could not obtaint the sizes of the widget

            return (height, width)

        # Make groups
        def get_group_dimensions(widget_list: list[etree._Element]):
            """
            Takes in a list of widget screens and finds the
            maximum height in the list
            """
            height_list = []
            width_list = []
            for widget in widget_list:
                root = etree.fromstring(str(widget), None)
                height: etree._Element | None = root.find("height")
                if height is not None:
                    height_list.append(
                        self.default_size if (val := height.text) is None else int(val)
                    )
                else:
                    height_list.append(self.default_size)

                width: etree._Element | None = root.find("width")
                if width is not None:
                    width_list.append(
                        self.default_size if (val := width.text) is None else int(val)
                    )
                else:
                    width_list.append(self.default_size)

            return (max(height_list) + group_padding, sum(width_list) + group_padding)

        # Create screen object
        self.screen_components = screen_components
        self.screen_ = Screen.Screen(self.screen_components[0].__class__.__name__)
        widgets = []
        groups = []

        self.P: str = "P"
        self.M: str = "M"

        # create widget and group objects
        widgets = []
        groups = []

        # Add group padding, and widget_x for placing widget in x direction relative to
        # other widgets, with a widget count to reset the widget_x dimension when the
        # allowed number of horizontal stacks is exceeded.
        group_padding = 40
        widget_x = 0
        widget_count = 0

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
                    widgets.append(
                        Widget.EmbeddedDisplay(
                            name,
                            "./techui-support/bob/" + screen[ui.type]["file"],
                            widget_x,
                            0,  # Change depending on the order
                            width,
                            height,
                        )
                    )
                    widget_x += width
                    widget_count += 1

                    # Reset X position after STACK_GLOBAL widgets
                    if widget_count % STACK_GLOBAL == 0:
                        widget_x = 0

                    # Add macros to the widgets
                    widgets[order].macro(self.P, ui.P)
                    widgets[order].macro(self.M, ui.M)

            if screen[ui.type]["type"] == "related":
                height, width = (40, 100)
                widgets.append(
                    Widget.ActionButton(
                        name,
                        name,
                        "{self.P:self.M}",
                        widget_x,
                        0,
                        width,
                        height,
                    )
                )
                widget_x += width
                widget_count += 1

                # Reset X position after STACK_GLOBAL widgets
                if widget_count % STACK_GLOBAL == 0:
                    widget_x = 0

                # Add action to action button: to open related display
                widgets[order].action_open_file(
                    f"./techui-support/bob/{screen[ui.type]['file']}"
                )

        # Create a widget list of widgets to be grouped based off how many can be tiled
        # together.
        widget_lists = [
            widgets[i : i + STACK_GLOBAL] for i in range(0, len(widgets), STACK_GLOBAL)
        ]

        # Create a list of dimensions for the groups
        # that will be created.
        group_heights_widths = []
        for widget_list in widget_lists:
            group_heights_widths.append(get_group_dimensions(widget_list))

        # Create the groups using the dimensions obtained from
        # group_heights_widths, making sure to stack the next group
        # vertically below the previous by incrementing the "y" value
        stack_height = 0
        for id, height_and_width in enumerate(group_heights_widths):
            groups.append(
                grp(
                    self.screen_components[0].__class__.__name__,
                    0,
                    stack_height,
                    height_and_width[1],
                    height_and_width[0],
                )
            )
            stack_height += height_and_width[0]
            groups[id].add_widget(widget_lists[id])

        # Add the created groups to the screen and write the screen
        self.screen_.add_widget(groups)
        self.screen_.write_screen(self.screen_components[0].__class__.__name__ + ".bob")
