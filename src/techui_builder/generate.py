import logging
import os
import random
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree, objectify
from phoebusgen import screen as pscreen
from phoebusgen import widget as pwidget
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay, Group

from techui_builder.models import Component, Entity, TechUi, TechUiSupport

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
            suffix_key = next(
                (k for k, v in component.macros.items() if v == suffix), None
            )
            if suffix_key is None:
                # Suffix not found in macros, use empty suffix
                raise ValueError("Suffix not in macros")
        except (IndexError, ValueError):
            prefix = component.prefix
            component_name = component.type
            suffix_key = suffix = ""

        # Try to get name from child labels if they exist,
        # if not, just use the name as it is.
        if component.child_labels is not None:
            if suffix in component.child_labels.keys():
                component_name = component.child_labels[suffix]
                self.label_flag = True

        prefix_key = next((k for k, v in component.macros.items() if v == prefix), None)
        if prefix_key is None:
            # Prefix not found in macros - skip this entity
            # This shouldn't happen with properly formed entities, but handle gracefully
            logger_.warning(
                f"Could not find P={prefix} in entity macros for {component.type}"
            )
            return component_name, {}

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

    def _new_widget_element(self, widget_type: str, **attrs) -> etree.Element:
        widget = etree.Element("widget", type=widget_type, version="2.0.0")
        for name, value in attrs.items():
            if value is None:
                continue
            child = etree.SubElement(widget, name)
            child.text = str(value)
        return widget

    def _make_color_element(
        self,
        parent: etree.Element,
        red: int,
        green: int,
        blue: int,
    ):
        color_el = etree.SubElement(parent, "color")
        color_el.set("red", str(red))
        color_el.set("green", str(green))
        color_el.set("blue", str(blue))
        return color_el

    def _create_beamline_widget(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int] = (0, 120, 215),
    ) -> etree.Element:
        widget = self._new_widget_element(
            "rectangle",
            name="BeamPipe",
            x=x,
            y=y,
            width=width,
            height=height,
            line_width=1,
        )
        line_color = etree.SubElement(widget, "line_color")
        self._make_color_element(
            line_color,
            *color,
        )
        background_color = etree.SubElement(widget, "background_color")
        self._make_color_element(background_color, *color)
        return widget

    def _get_available_symbols(self) -> list[Path]:
        """Get list of available symbol SVG files."""
        symbols_dir = self.support_path.joinpath("symbols")
        if symbols_dir.exists():
            return sorted(symbols_dir.glob("*.svg"))
        return []

    def _create_symbol_widget(
        self,
        label: str,
        symbol_path: Path,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> etree.Element:
        """Create a symbol widget with display action."""
        # Make symbol path relative to synoptic dir
        try:
            rel_symbol_path = symbol_path.relative_to(
                self.synoptic_dir,
                walk_up=True,
            )
        except ValueError:
            rel_symbol_path = symbol_path

        widget = self._new_widget_element(
            "symbol",
            name=label,
            x=x,
            y=y,
            width=width,
            height=height,
            pv_name=label,
        )
        symbols = etree.SubElement(widget, "symbols")
        symbol = etree.SubElement(symbols, "symbol")
        symbol.text = str(rel_symbol_path)
        return widget

    def _create_label_widget(
        self,
        label: str,
        x: int,
        y: int,
        width: int = 80,
    ) -> etree.Element:
        """Create a label widget centered below a component symbol."""
        # Center label under icon by offsetting its x position
        label_x = x - (width - 60) // 2
        widget = self._new_widget_element(
            "label",
            name=f"Label_{label}",
            text=label,
            x=label_x,
            y=y,
            width=width,
            horizontal_alignment="1",
        )
        return widget

    def _create_component_widget(
        self,
        component_name: str,
        label: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> etree.Element:
        """Create a symbol widget with display action."""
        widget = self._new_widget_element(
            "action_button",
            name=label,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        actions = etree.SubElement(widget, "actions")
        action = etree.SubElement(actions, "action")
        action.set("type", "open_display")
        file_el = etree.SubElement(action, "file")
        file_el.text = f"{component_name}.bob"
        target_el = etree.SubElement(action, "target")
        target_el.text = "replace"
        desc_el = etree.SubElement(action, "description")
        desc_el.text = "Open Display"
        return widget

    def _format_pipe_section(
        self,
        display: etree.Element,
        section_name: str,
        component_names: list[str],
        components: dict[str, Component],
        pipe_left: int,
        pipe_top: int,
        pipe_width: int,
        pipe_height: int,
        button_y: int,
        color: tuple[int, int, int],
    ) -> None:
        """Add a pipe line and ordered components to the display."""
        display.append(
            self._create_beamline_widget(
                pipe_left,
                pipe_top,
                pipe_width,
                pipe_height,
                color,
            )
        )

        if not component_names:
            return

        available_symbols = self._get_available_symbols()
        symbol_width = 60
        symbol_height = 60
        # label_height = 20
        count = len(component_names)
        spacing = int((pipe_width - count * symbol_width) / (count + 1))
        spacing = max(20, spacing)

        x = pipe_left + spacing
        for component_name in component_names:
            component = components[component_name]
            label = component.label or component_name
            symbol_path = (
                random.choice(available_symbols) if available_symbols else None
            )
            if symbol_path:
                display.append(
                    self._create_symbol_widget(
                        label,
                        symbol_path,
                        x,
                        button_y,
                        symbol_width,
                        symbol_height,
                    )
                )
            display.append(
                self._create_label_widget(
                    label,
                    x,
                    button_y + symbol_height + 5,
                )
            )
            x += symbol_width + spacing

    def generate_index_bob(
        self,
        techui: TechUi,
        output_dir: Path | None = None,
    ) -> None:
        """Generate an index.bob from ordered components in techui.yaml."""
        if output_dir is None:
            output_dir = self.synoptic_dir

        if not techui.beam_pipe and not techui.vacuum_pipe:
            logger_.warning(
                "No beam_pipe or vacuum_pipe sections defined; "
                "skipping index.bob generation."
            )
            return

        pipe_left = 100
        pipe_width = 1200
        pipe_height = 8
        display = etree.Element("display", version="2.0.0")
        title = etree.SubElement(display, "name")
        title.text = techui.beamline.location

        if techui.vacuum_pipe:
            self._format_pipe_section(
                display,
                "vacuum_pipe",
                techui.vacuum_pipe,
                techui.components,
                pipe_left,
                120,
                pipe_width,
                pipe_height,
                80,
                (180, 180, 180),
            )

        if techui.beam_pipe:
            self._format_pipe_section(
                display,
                "beam_pipe",
                techui.beam_pipe,
                techui.components,
                pipe_left,
                260,
                pipe_width,
                pipe_height,
                220,
                (0, 120, 215),
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir.joinpath("index.bob")
        tree = etree.ElementTree(display)
        tree.write(
            output_path,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )
        logger_.info(f"Generated index.bob at {output_path}")

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
