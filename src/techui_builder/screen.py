from dataclasses import dataclass, field

# import warnings
from lxml import etree, objectify  # type: ignore
from phoebusgen import screen as Screen
from phoebusgen import widget as Widget
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay, Group

from techui_builder.datatypes import Entry

STACK_GLOBAL = 5


@dataclass
class Generator:
    screen_components: list[Entry]
    # TODO: Fix type of screen
    screen: dict

    # These are global params for the class (not accessible by user)
    default_size: int = field(default=100, init=False, repr=False)
    P: str = field(default="P", init=False, repr=False)
    M: str = field(default="M", init=False, repr=False)
    groups: list[Group] = field(default_factory=list[Group], init=False, repr=False)

    # Add group padding, and self.widget_x for placing widget in x direction relative to
    # other widgets, with a widget count to reset the self.widget_x dimension when the
    # allowed number of horizontal stacks is exceeded.
    widget_x: int = field(default=0, init=False, repr=False)
    widget_count: int = field(default=0, init=False, repr=False)
    group_padding: int = field(default=40, init=False, repr=False)

    def _get_screen_dimensions(self, file: str) -> tuple[int, int]:
        """
        Parses the bob files for information on the height
        and width of the screen
        """
        parser = etree.XMLParser()
        # Read the bob file
        tree: etree._ElementTree = objectify.parse(file, parser)
        root: etree._Element = tree.getroot()
        height_element: etree._Element | None = root.find("height", namespaces=None)
        if height_element is not None:
            height = (
                self.default_size if (val := height_element.text) is None else int(val)
            )
        else:
            height = self.default_size
            # Assert that could not obtaint the sizes of the widget

        width_element: etree._Element | None = root.find("width", namespaces=None)
        if width_element is not None:
            width = (
                self.default_size if (val := width_element.text) is None else int(val)
            )
        else:
            width = self.default_size
            # Assert that could not obtaint the sizes of the widget

        return (height, width)

    # Make groups
    def _get_group_dimensions(self, widget_list: list[EmbeddedDisplay | ActionButton]):
        """
        Takes in a list of widget screens and finds the
        maximum height in the list
        """
        height_list: list[int] = []
        width_list: list[int] = []
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

        return (
            max(height_list) + self.group_padding,
            sum(width_list) + self.group_padding,
        )

    def _create_widget(self, component: Entry) -> EmbeddedDisplay | ActionButton:
        # if statement below is check if the suffix is
        # missing from the component description. If
        # not missing, use as name of widget, if missing,
        # use type as name.
        if component.M is not None:
            name = component.M
        else:
            name = component.type

        # Get dimensions of screen from TechUI repository
        if self.screen[component.type]["type"] == "embedded":
            height, width = self._get_screen_dimensions(
                f"./techui-support/bob/{self.screen[component.type]['file']}"
            )

            new_widget = Widget.EmbeddedDisplay(
                name,
                "../techui-support/bob/" + self.screen[component.type]["file"],
                self.widget_x,
                0,  # Change depending on the order
                width,
                height,
            )

            if height or width is not None:
                self.widget_x += width
                self.widget_count += 1

                # Reset X position after STACK_GLOBAL widgets
                if self.widget_count % STACK_GLOBAL == 0:
                    self.widget_x = 0

                # Add macros to the widgets
                new_widget.macro(self.P, component.P)
                new_widget.macro(self.M, component.M or "")

        # elif self.screen[component.type]["type"] == "related":
        else:
            height, width = (40, 100)

            new_widget = Widget.ActionButton(
                name,
                name,
                f"{component.P}:{component.M}",
                self.widget_x,
                0,
                width,
                height,
            )

            self.widget_x += width
            self.widget_count += 1

            # Reset X position after STACK_GLOBAL widgets
            if self.widget_count % STACK_GLOBAL == 0:
                self.widget_x = 0

            # Add action to action button: to open related display
            new_widget.action_open_display(
                file=f"../techui-support/bob/{self.screen[component.type]['file']}",
                target="tab",
                macros={"P": component.P, "M": component.M},
            )

        return new_widget

    def build_groups(self):
        # Create screen object
        self.screen_ = Screen.Screen(
            str(self.screen_components[0].file).removesuffix(".bob")
        )

        # create widget and group objects
        widgets: list[EmbeddedDisplay | ActionButton] = []

        # order is an enumeration of the components, used to list them,
        # and serves as functionality in the math for formatting.
        for component in self.screen_components:
            new_widget = self._create_widget(component=component)

            widgets.append(new_widget)

        # Create a widget list of widgets to be grouped based off how many can be tiled
        # together.
        widget_groups = [
            widgets[i : i + STACK_GLOBAL] for i in range(0, len(widgets), STACK_GLOBAL)
        ]

        # Create a list of dimensions for the groups
        # that will be created.
        group_dims = []
        for widget_list in widget_groups:
            group_dims.append(self._get_group_dimensions(widget_list))

        # Create the groups using the dimensions obtained from
        # group_dims, making sure to stack the next group
        # vertically below the previous by incrementing the "y" value
        stack_height: int = 0
        for id, dims in enumerate(group_dims):
            height, width = dims
            self.groups.append(
                Group(
                    str(self.screen_components[0].file).removesuffix(".bob"),
                    0,
                    stack_height,
                    width,
                    height,
                )
            )
            stack_height += height
            self.groups[id].version("2.0.0")
            self.groups[id].add_widget(widget_groups[id])

    def write_screen(self):
        # Add the created groups to the screen and write the screen
        self.screen_.add_widget(self.groups)
        self.screen_.write_screen(
            "./example-synoptic/" + str(self.screen_components[0].file)
        )
