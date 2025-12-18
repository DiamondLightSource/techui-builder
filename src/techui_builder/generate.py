import logging
import os
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from lxml import objectify
from phoebusgen import screen as pscreen
from phoebusgen import widget as pwidget
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay, Group

from techui_builder.models import Entity

logger_ = logging.getLogger(__name__)


@dataclass
class Generator:
    synoptic_dir: Path = field(repr=False)
    beamline_url: str = field(repr=False)

    # These are global params for the class (not accessible by user)
    support_path: Path = field(init=False, repr=False)
    techui_support: dict = field(init=False, repr=False)
    default_size: int = field(default=100, init=False, repr=False)
    P: str = field(default="P", init=False, repr=False)
    M: str = field(default="M", init=False, repr=False)
    R: str = field(default="R", init=False, repr=False)
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

    def __post_init__(self):
        # This needs to be before _read_map()
        self.support_path = self.synoptic_dir.joinpath("techui-support")

        self._read_map()

    def _read_map(self):
        """Read the techui-support.yaml file from techui-support."""
        support_yaml = self.support_path.joinpath("techui-support.yaml").absolute()
        logger_.debug(f"techui-support.yaml location: {support_yaml}")

        with open(support_yaml) as map:
            self.techui_support = yaml.safe_load(map)

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

    def _initialise_name_suffix(self, component: Entity) -> tuple[str, str, str | None]:
        if component.M is not None:
            name: str = component.M
            suffix: str = component.M
            suffix_label: str | None = self.M
        elif component.R is not None:
            name = component.R
            suffix = component.R
            suffix_label = self.R
        else:
            name = component.P
            suffix = ""
            suffix_label = ""

        return (name, suffix, suffix_label)

    def _is_list_of_dicts(self, scrn_mapping: Mapping) -> bool:
        return isinstance(scrn_mapping, Sequence) and all(
            isinstance(scrn, Mapping) for scrn in scrn_mapping
        )

    def _allocate_widget(
        self, scrn_mapping: Mapping, component: Entity
    ) -> EmbeddedDisplay | ActionButton | None | list[EmbeddedDisplay | ActionButton]:
        name, suffix, suffix_label = self._initialise_name_suffix(component)
        # Get relative path to screen
        scrn_path = self.support_path.joinpath(f"bob/{scrn_mapping['file']}")
        logger_.debug(f"Screen path: {scrn_path}")

        # Path of screen relative to data/ so it knows where to open the file from
        data_scrn_path = scrn_path.relative_to(self.synoptic_dir, walk_up=True)

        # For Gui Components with multiple components embedded, we add a suffix field
        # to the components, and adjust the name and suffix accordingly
        try:
            if scrn_mapping["suffix"] is not None:
                suffix: str = scrn_mapping["suffix"]
                match: re.Match[str] | None = re.match(
                    r"^\$\(([A-Z])\)\$\(([A-Z])\)$", scrn_mapping["prefix"]
                )
                if match:
                    suffix_label: str | None = match.group(2)
                    name: str = suffix
        except KeyError:
            pass

        if scrn_mapping["type"] == "embedded":
            height, width = self._get_screen_dimensions(str(scrn_path))
            new_widget = pwidget.EmbeddedDisplay(
                name.removeprefix(":").removesuffix(":"),
                str(data_scrn_path),
                0,
                0,  # Change depending on the order
                width,
                height,
            )
            # Add macros to the widgets
            new_widget.macro(self.P, component.P)
            if suffix_label != "":
                new_widget.macro(
                    f"{suffix_label}", suffix.removeprefix(":").removesuffix(":")
                )
            # TODO: Change this to pvi_button
            if True:
                new_widget.macro("IOC", f"{self.beamline_url}/{component.P.lower()}")

        # The only other option is for related displays
        else:
            height, width = (40, 100)

            new_widget = pwidget.ActionButton(
                name.removeprefix(":").removesuffix(":"),
                name.removeprefix(":").removesuffix(":"),
                "",
                0,
                0,
                width,
                height,
            )

            # Add action to action button: to open related display
            if suffix_label != "":
                new_widget.action_open_display(
                    file=str(data_scrn_path),
                    target="tab",
                    macros={
                        "P": component.P,
                        f"{suffix_label}": suffix,
                    },
                )
            else:
                new_widget.action_open_display(
                    file=str(data_scrn_path),
                    target="tab",
                    macros={
                        "P": component.P,
                    },
                )

            # For some reason the version of action buttons is 3.0.0?
            new_widget.version("2.0.0")
        return new_widget

    def _create_widget(
        self, name: str, component: Entity
    ) -> EmbeddedDisplay | ActionButton | None | list[EmbeddedDisplay | ActionButton]:
        # if statement below is check if the suffix is
        # missing from the component description. If
        # not missing, use as name of widget, if missing,
        # use type as name.
        new_widget = []

        try:
            scrn_mapping = self.techui_support[component.type]
        except KeyError:
            logger_.warning(
                f"No available widget for {component.type} in screen \
{name}. Skipping..."
            )
            return None

        if self._is_list_of_dicts(scrn_mapping):
            for value in scrn_mapping:
                new_widget.append(self._allocate_widget(value, component))
        else:
            new_widget = self._allocate_widget(scrn_mapping, component)

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

    def build_widgets(self, screen_name: str, screen_components: list[Entity]):
        # Empty widget buffer
        self.widgets = []

        # order is an enumeration of the components, used to list them,
        # and serves as functionality in the math for formatting.
        for component in screen_components:
            new_widget = self._create_widget(name=screen_name, component=component)
            if new_widget is None:
                continue
            if isinstance(new_widget, list):
                self.widgets.extend(new_widget)
                continue
            self.widgets.append(new_widget)

    def build_groups(self, screen_name: str):
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

        self.group = Group(
            screen_name,
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
