"""Links from a .bob screen to other screens."""

import logging
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from lxml.objectify import ObjectifiedElement

from techui_builder.utils import (
    WidgetType,
    _get_action_group,
    _get_macros,
    _get_nav_tabs,
)

logger_ = logging.getLogger(__name__)

MACRO_RE = re.compile(r"\$(?:\((\w+)\)|\{(\w+)\})")


@dataclass
class WidgetLink:
    """A link from a .bob screen to another screen."""

    file: str  # raw, stripped <file> text
    name: str | None  # widget <name> (or tab <name>)
    type: WidgetType
    macros: dict[str, str]


def extract_file_text(file_elem: ObjectifiedElement) -> str:
    """The stripped text of a <file> element."""
    # Keep the raw string; macros are expanded later
    return file_elem.text.strip() if file_elem.text else ""


def is_bob(file: str) -> bool:
    """Whether the link is to a .bob screen"""
    return file.endswith(".bob")


def extract_links(root: ObjectifiedElement) -> Iterator[WidgetLink]:
    """Yield links to .bob screens from widgets, in document order."""
    # Find all <widget> elements
    widgets = [
        w
        for w in root.findall(".//widget")
        if w.get("type", default=None) in WidgetType
    ]

    # A generator, so an error in a widget is raised after earlier links are crawled
    for widget_elem in widgets:
        widget_type = WidgetType(widget_elem.get("type"))

        match widget_type:
            case WidgetType.SYMBOL | WidgetType.ACTION_BUTTON:
                # Only the first open_display action; skip widgets without one
                open_display = _get_action_group(widget_elem)
                if open_display is None:
                    continue

                # Use file, name, and macro elements
                file_elem = open_display.file
                name = widget_elem.name.text
                macros = _get_macros(open_display)

            case WidgetType.EMBEDDED:
                file_elem = widget_elem.file
                name = widget_elem.name.text
                macros = _get_macros(widget_elem)

            case WidgetType.NAVTABS:
                # One link per tab, in tab order
                tabs = _get_nav_tabs(widget_elem)
                if tabs is None:
                    continue

                for tab in tabs:
                    name = tab.name.text
                    file_elem = tab.file
                    macros = _get_macros(tab)

                    file = extract_file_text(file_elem)
                    # Skip links that are not .bob screens
                    if not is_bob(file):
                        logger_.debug(f"Skipping link to {file}: not a .bob screen")
                        continue

                    yield WidgetLink(file, name, widget_type, macros)

                continue

            # If a widget is valid but not valid in this context
            case _:
                continue

        file = extract_file_text(file_elem)
        # Skip links that are not .bob screens
        if not is_bob(file):
            logger_.debug(f"Skipping link to {file}: not a .bob screen")
            continue

        yield WidgetLink(file, name, widget_type, macros)


def substitute_macros(text: str, macros: Mapping[str, str]) -> str:
    """Replace $(NAME) and ${NAME} with macro values, leaving unknown macros as-is."""
    return MACRO_RE.sub(
        lambda m: macros.get(m.group(1) or m.group(2), m.group(0)), text
    )


def resolve_link(file: str, macros: Mapping[str, str], screen: Path) -> Path:
    """Resolve a link's file to a local path, relative to the linking screen."""
    file = substitute_macros(file, macros)
    # Phoebus resolves relative files against the display containing the link
    return screen.parent / file
