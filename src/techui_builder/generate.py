import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from lxml import etree, objectify  # type: ignore
from phoebusgen import screen as Screen
from phoebusgen import widget as Widget
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay, Group

from techui_builder.objects import Entity

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))


@dataclass
class Generator:
    screen_components: list[Entity]
    # TODO: Fix type of screen
    screen_name: str

    # These are global params for the class (not accessible by user)
    gui_map: dict = field(init=False, repr=False)
    default_size: int = field(default=100, init=False, repr=False)
    P: str = field(default="P", init=False, repr=False)
    M: str = field(default="M", init=False, repr=False)
    R: str = field(default="R", init=False, repr=False)
    widgets: list[ActionButton | EmbeddedDisplay] = field(
        default_factory=list[ActionButton | EmbeddedDisplay], init=False, repr=False
    )

    # Add group padding, and self.widget_x for placing widget in x direction relative to
    # other widgets, with a widget count to reset the self.widget_x dimension when the
    # allowed number of horizontal stacks is exceeded.
    widget_x: int = field(default=0, init=False, repr=False)
    widget_count: int = field(default=0, init=False, repr=False)
    group_padding: int = field(default=50, init=False, repr=False)

    def __post_init__(self):
        self._read_gui_map()

    def _read_gui_map(self):
        """Read the gui_map.yaml file from techui-support."""
        gui_map = Path(__file__).parent.parent.joinpath(
            "../techui-support/gui_map.yaml"
        )

        with open(gui_map) as map:
            self.gui_map = yaml.safe_load(map)

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
            assert "Could not obtain the size of the widget"

        width_element: etree._Element | None = root.find("width", namespaces=None)
        if width_element is not None:
            width = (
                self.default_size if (val := width_element.text) is None else int(val)
            )
        else:
            width = self.default_size
            assert "Could not obtain the size of the widget"

        return (height, width)

    def _get_widget_dimensions(
        self, widget: EmbeddedDisplay | ActionButton
    ) -> tuple[int, int]:
        """
        Parses the widget for information on the height
        and width of the widget
        """
        # Read the bob file
        root: etree._Element = etree.fromstring(str(widget), None)
        height_element: etree._Element | None = root.find("height", namespaces=None)
        if height_element is not None:
            height = (
                self.default_size if (val := height_element.text) is None else int(val)
            )
        else:
            height = self.default_size
            assert "Could not obtain the size of the widget"

        width_element: etree._Element | None = root.find("width", namespaces=None)
        if width_element is not None:
            width = (
                self.default_size if (val := width_element.text) is None else int(val)
            )
        else:
            width = self.default_size
            assert "Could not obtain the size of the widget"

        return (height, width)

    def _get_widget_position(
        self, object: EmbeddedDisplay | ActionButton
    ) -> tuple[int, int]:
        """
        Parses the widget for information on the y
        and x of the widget
        """
        # Read the bob file
        root: etree._Element = etree.fromstring(str(object), None)
        y_element: etree._Element | None = root.find("y", namespaces=None)
        if y_element is not None:
            y = self.default_size if (val := y_element.text) is None else int(val)
        else:
            y = self.default_size
            assert "Could not obtain the size of the widget"

        x_element: etree._Element | None = root.find("x", namespaces=None)
        if x_element is not None:
            x = self.default_size if (val := x_element.text) is None else int(val)
        else:
            x = self.default_size
            assert "Could not obtain the size of the widget"

        return (y, x)

    # Make groups
    def _get_group_dimensions(self, widget_list: list[EmbeddedDisplay | ActionButton]):
        """
        Takes in a list of widgets and finds the
        maximum height in the list
        """
        x_list: list[int] = []
        y_list: list[int] = []
        height_list: list[int] = []
        width_list: list[int] = []
        for widget in widget_list:
            root = etree.fromstring(str(widget), None)
            x: etree._Element | None = root.find("x")
            if x is not None:
                x_list.append(
                    self.default_size if (val := x.text) is None else int(val)
                )
            else:
                x_list.append(self.default_size)

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

            y: etree._Element | None = root.find("y")
            if y is not None:
                y_list.append(
                    self.default_size if (val := y.text) is None else int(val)
                )
            else:
                y_list.append(self.default_size)

        return (
            max(y_list) + max(height_list) + self.group_padding,
            max(x_list) + max(width_list) + self.group_padding,
        )

    def _create_widget(
        self, component: Entity
    ) -> EmbeddedDisplay | ActionButton | None:
        # if statement below is check if the suffix is
        # missing from the component description. If
        # not missing, use as name of widget, if missing,
        # use type as name.
        if component.M is not None:
            name: str = component.M
            suffix: str = component.M
            suffix_label: str | None = self.M
        elif component.R is not None:
            name = component.R
            suffix = component.R
            suffix_label = self.R
        else:
            name = component.type
            suffix = ""
            suffix_label = None

        try:
            # Get dimensions of screen from TechUI repository
            if self.gui_map[component.type]["type"] == "embedded":
                height, width = self._get_screen_dimensions(
                    f"./techui-support/bob/{self.gui_map[component.type]['file']}"
                )

                new_widget = Widget.EmbeddedDisplay(
                    name,
                    "../../techui-support/bob/" + self.gui_map[component.type]["file"],
                    0,
                    0,  # Change depending on the order
                    width,
                    height,
                )
                # Add macros to the widgets
                new_widget.macro(self.P, component.P)
                if suffix_label is not None:
                    new_widget.macro(f"{suffix_label}", suffix)

            # The only other option is for related displays
            else:
                height, width = (40, 100)

                new_widget = Widget.ActionButton(
                    name,
                    component.P,
                    f"{component.P}:{suffix_label}",
                    0,
                    0,
                    width,
                    height,
                )

                # Add action to action button: to open related display
                if suffix_label is not None:
                    new_widget.action_open_display(
                        file=f"../../techui-support/bob/{self.gui_map[component.type]['file']}",
                        target="tab",
                        macros={
                            "P": component.P,
                            f"{suffix_label}": suffix,
                        },
                    )
                else:
                    new_widget.action_open_display(
                        file=f"../../techui-support/bob/{self.gui_map[component.type]['file']}",
                        target="tab",
                        macros={
                            "P": component.P,
                        },
                    )
        except KeyError:
            LOGGER.info(f"No available widget for {name} in screen {self.screen_name}")
            new_widget = None

        return new_widget

    def layout_widgets(self, widgets: list[EmbeddedDisplay | ActionButton]):
        group_spacing: int = 30
        max_group_height: int = 800
        spacing_x: int = 20
        spacing_y: int = 30
        # Group tiles by size
        groups: dict[tuple[int, int], list[EmbeddedDisplay | ActionButton]] = (
            defaultdict(list)
        )
        for widget in widgets:
            key = self._get_widget_dimensions(widget)

            groups[key].append(widget)

        # Sort groups by width (optional)
        sorted_widgets: list[EmbeddedDisplay | ActionButton] = []
        sorted_groups = sorted(groups.items(), key=lambda g: g[0][0], reverse=True)
        current_x: int = 0
        current_y: int = 0
        column_width: int = 0
        column_levels: list[list[EmbeddedDisplay | ActionButton]] = []

        for (h, w), group in sorted_groups:
            for widget in group:
                placed = False
                for level in column_levels:
                    level_y, _ = self._get_widget_position(level[0])
                    _, widget_width = self._get_widget_dimensions(widget)
                    level_width = (
                        sum(
                            (self._get_widget_dimensions(t))[1] + spacing_x
                            for t in level
                        )
                        - spacing_x
                    )  # Find the width of the row
                    if (
                        level_y + h <= max_group_height
                        and level_width + widget_width <= column_width
                    ):
                        _, width_1 = self._get_widget_dimensions(level[-1])
                        _, x_1 = self._get_widget_position(level[-1])
                        widget.x(x_1 + width_1 + spacing_x)
                        widget.y(level_y)
                        level.append(widget)
                        placed = True
                        break

                if not placed:
                    if current_y + h > max_group_height:
                        # Moves to the next column
                        current_x += column_width + group_spacing
                        current_y = 0
                        column_width = 0
                        column_levels = []
                    # Places widgets in rows in one column
                    widget.x(current_x)
                    widget.y(current_y)
                    column_levels.append([widget])
                    current_y += h + spacing_y
                    column_width = max(column_width, w)
                sorted_widgets.append(widget)

        return sorted_widgets

    def build_groups(self):
        """
        Create a group to fill with widgets
        """
        # Create screen
        self.screen_ = Screen.Screen(self.screen_name)
        # create widget and group objects

        # order is an enumeration of the components, used to list them,
        # and serves as functionality in the math for formatting.
        for component in self.screen_components:
            new_widget = self._create_widget(component=component)
            if new_widget is None:
                continue
            self.widgets.append(new_widget)

        if self.widgets == []:
            # No widgets found, so just back out
            return

        self.widgets = self.layout_widgets(self.widgets)

        # Create a list of dimensions for the groups
        # that will be created.
        height, width = self._get_group_dimensions(self.widgets)

        self.group = Group(
            self.screen_name,
            0,
            0,
            width,
            height,
        )

        self.group.version("2.0.0")
        self.group.add_widget(self.widgets)
        self.screen_.add_widget(self.group)

    def write_screen(self, directory: Path):
        """Write the screen to file"""

        if self.widgets == []:
            LOGGER.info(
                f"Could not write screen: {self.screen_name} \
as no widgets were available"
            )
            return

        if not directory.exists():
            os.mkdir(directory)
        self.screen_.write_screen(f"{directory}/{self.screen_name}.bob")
        LOGGER.info(f"{self.screen_name}.bob has been created successfully")
