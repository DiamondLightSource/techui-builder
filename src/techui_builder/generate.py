import logging
import os
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from lxml import objectify
from phoebusgen import screen as pscreen
from phoebusgen import widget as pwidget
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay, Group

from techui_builder.models import Component, Entity, TechUiSupport

logger_ = logging.getLogger(__name__)


@dataclass
class Generator:
    synoptic_dir: Path = field(repr=False)
    beamline_url: str = field(repr=False)

    # These are global params for the class (not accessible by user)
    support_path: Path = field(repr=False)
    techui_support: TechUiSupport = field(repr=False)
    default_size: int = field(default=100, init=False, repr=False)
    prefix: str = field(default="P", init=False, repr=False)
    widgets: list[ActionButton | EmbeddedDisplay] = field(
        default_factory=list[ActionButton | EmbeddedDisplay], init=False, repr=False
    )
    group: Group | None = field(default=None, init=False, repr=False)

    # Add group padding, and self.widget_x for placing widget in x direction relative to
    # other widgets, with a widget count to reset the self.widget_x dimension when the
    # allowed number of horizontal stacks is exceeded.
    widget_x: int = field(default=0, init=False, repr=False)
    widget_count: int = field(default=0, init=False, repr=False)
    group_padding: int = field(default=50, init=False, repr=False)
    label_flag: bool = field(default=False, init=False, repr=False)

    def _get_screen_dimensions(self, file: str) -> tuple[int, int]:
        """
        Parses the bob files for information on the height
        and width of the screen
        """
        # Read the bob file
        tree = objectify.parse(file)
        root = tree.getroot()
        try:
            height_element = root.height
            height = (
                self.default_size if (val := height_element.text) is None else int(val)
            )
        except AttributeError:
            height = self.default_size
            assert "Could not obtain the height of the widget"

        try:
            width_element = root.width
            width = (
                self.default_size if (val := width_element.text) is None else int(val)
            )
        except AttributeError:
            width = self.default_size
            assert "Could not obtain the width of the widget"

        return (height, width)

    def _get_widget_dimensions(
        self, widget: EmbeddedDisplay | ActionButton
    ) -> tuple[int, int]:
        """
        Parses the widget for information on the height
        and width of the widget
        """
        # Read the bob file
        root = objectify.fromstring(str(widget))
        try:
            height_element = root.height
            height = (
                self.default_size if (val := height_element.text) is None else int(val)
            )
        except AttributeError:
            height = self.default_size
            assert "Could not obtain the size of the widget"

        try:
            width_element = root.width
            width = (
                self.default_size if (val := width_element.text) is None else int(val)
            )
        except AttributeError:
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
        root = objectify.fromstring(str(object))

        try:
            y_element = root.y
            y = self.default_size if (val := y_element.text) is None else int(val)
        except AttributeError:
            y = self.default_size
            assert "Could not obtain the size of the widget"

        try:
            x_element = root.x
            x = self.default_size if (val := x_element.text) is None else int(val)
        except AttributeError:
            x = self.default_size
            assert "Could not obtain the size of the widget"

        return (y, x)

    # Make groups
    def _get_group_dimensions(self, widget_list: list[EmbeddedDisplay | ActionButton]):
        """
        Takes in a list of widgets and finds the
        maximum height and maximum width in the list
        """
        width_list: list[int] = []
        height_list: list[int] = []
        for widget in widget_list:
            y, x = self._get_widget_position(widget)
            height, width = self._get_widget_dimensions(widget)
            comparable_width = x + width
            comparable_height = y + height
            width_list.append(comparable_width)
            height_list.append(comparable_height)

        return (
            max(height_list) + self.group_padding,
            max(width_list) + self.group_padding,
        )

    def _update_macros(self, component: Entity) -> tuple[str, dict[str, str]]:
        # try statement below is check if the suffix is part of the component prefix.
        # If not missing, use as name of widget. If missing, use type as name.

        new_macros = {}

        try:
            # re.split() returns the remainder as the final element,
            # so this needs to be ignored
            prefix, suffix = re.split(r"(:[A-Z0-9:]+)", component.prefix, maxsplit=1)[
                :2
            ]
            component_name = suffix.removeprefix(":").removesuffix(":")
            suffix_key = next(k for k, v in component.macros.items() if v == suffix)
        except (IndexError, ValueError):
            prefix = component.prefix
            component_name = component.type
            suffix_key = suffix = ""

        # Try to get name from child labels if they exist,
        # if not, just use the name as it is.
        if component.child_labels is not None:
            if component_name in component.child_labels.keys():
                component_name = component.child_labels[component_name]
                self.label_flag = True

        prefix_key = next(k for k, v in component.macros.items() if v == prefix)

        new_macros[prefix_key] = prefix
        if suffix_key != "":
            new_macros[suffix_key] = suffix
            new_macros["label"] = component_name

        return component_name, new_macros

    def _allocate_widget(
        self, screen_mapping: Mapping, component: Entity
    ) -> EmbeddedDisplay | ActionButton | None | list[EmbeddedDisplay | ActionButton]:
        component_name, updated_macros = self._update_macros(component)

        # Get relative path to screen
        file = screen_mapping["file"]
        if file.startswith("$(IOC)"):
            screen_path = support_screen_path = file.replace(
                "$(IOC)", f"{self.beamline_url}/{component.service_name}"
            )  # Only works with related displays as
            # embedded displays need to access the file to get dimensions

            assert screen_mapping["type"] == "related", (
                "Only related displays can have remote screens"
            )
        else:
            screen_path = self.support_path.joinpath(f"bob/{file}")
            logger_.debug(f"Screen path: {screen_path}")

            # Path of screen relative to synoptic/
            support_screen_path = screen_path.relative_to(
                self.synoptic_dir, walk_up=True
            )

        # For Gui Components with multiple components embedded, we add a suffix field
        # to the components, and adjust the name and suffix accordingly
        try:
            if screen_mapping["suffixes"] is not None:
                suffix_dict: dict[str, str] = screen_mapping["suffixes"]
                for suffix_key, suffix in suffix_dict.items():
                    updated_macros[suffix_key] = suffix

                # If no child label was specified...
                if self.label_flag is False:
                    # TODO: think of a better fallback component name for this
                    component_name = (
                        list(suffix_dict.values())[0]
                        .removeprefix(":")
                        .removesuffix(":")
                    )
                    updated_macros["label"] = component_name
        except KeyError:
            pass

        if screen_mapping["type"] == "embedded":
            height, width = self._get_screen_dimensions(str(screen_path))
            new_widget = pwidget.EmbeddedDisplay(
                component_name,
                str(support_screen_path),
                0,
                0,  # Change depending on the order
                width,
                height,
            )
            # Add macros to the widgets
            for macro, macro_val in updated_macros.items():
                new_widget.macro(macro, macro_val)

            # TODO: Change this to pvi_button
            if True:
                new_widget.macro("IOC", f"{self.beamline_url}/{component.service_name}")

        # The only other option is for related displays
        else:
            height, width = (40, 100)

            new_widget = pwidget.ActionButton(
                component_name,
                component_name,
                "",
                0,
                0,
                width,
                height,
            )

            # Add action to action button: to open related display

            new_widget.action_open_display(
                file=str(support_screen_path), target="tab", macros=updated_macros
            )

            # For some reason the version of action buttons is 3.0.0?
            new_widget.version("2.0.0")
            self.label_flag = False
        return new_widget

    def _create_widgets(
        self, name: str, component: Entity
    ) -> list[EmbeddedDisplay | ActionButton] | None:
        new_widget = []

        try:
            screen_mapping = self.techui_support.support_modules[component.type].screens
        except KeyError:
            logger_.warning(
                f"No available widget for {component.type} in screen \
{name}. Skipping..."
            )
            return None

        for screen_dict in screen_mapping:
            new_widget.append(self._allocate_widget(screen_dict, component))

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

    def build_widgets(self, screen_name: str, screen_entities: list[Entity]):
        # Empty widget buffer
        self.widgets = []

        # order is an enumeration of the components, used to list them,
        # and serves as functionality in the math for formatting.
        for entity in screen_entities:
            new_widgets = self._create_widgets(name=screen_name, component=entity)
            if new_widgets is None:
                continue
            self.widgets.extend(new_widgets)

    def build_groups(self, screen_name: str, builder_components: dict[str, Component]):
        """
        Create a group to fill with widgets
        """

        if self.widgets == []:
            # No widgets found, so just back out
            return

        self.widgets = self.layout_widgets(self.widgets)
        # Create a list of dimensions for the groups
        # that will be created.
        height, width = self._get_group_dimensions(self.widgets)

        if (
            screen_name in builder_components.keys()
            and builder_components[screen_name].label is not None
        ):
            label = builder_components[screen_name].label or screen_name
        else:
            label = screen_name

        self.group = Group(
            label,
            0,
            0,
            width,
            height,
        )

        # TODO: we shouldn't need this assert; fix
        assert self.group is not None
        self.group.version("2.0.0")
        self.group.add_widget(self.widgets)

    def build_screen(self, screen_name):
        """
        Build the screen with the widget groups.
        """
        # Create screen
        self.screen_ = pscreen.Screen(screen_name)

        # TODO: I don't like this
        if self.group is None:
            # No group found, so just back out
            return

        self.screen_.add_widget(self.group)

    def write_screen(self, screen_name: str, directory: Path):
        """Write the screen to file"""

        if self.widgets == []:
            logger_.warning(
                f"Could not write screen: {screen_name} \
as no widgets were available"
            )
            return

        if not directory.exists():
            os.mkdir(directory)
        self.screen_.write_screen(f"{directory}/{screen_name}.bob")
        logger_.info(f"{screen_name}.bob has been created successfully")
