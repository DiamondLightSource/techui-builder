"""Links from a .bob screen to other screens."""

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from lxml.objectify import ObjectifiedElement

from techui_builder.utils import _get_action_group, _get_macros, _get_nav_tabs

PVI_FILE_RE = re.compile(r"^(?:\$\(IOC\))\/([a-zA-Z]+[.a-zA-Z]+)$")


class WidgetType(StrEnum):
    """Widget types in a .bob file that can link to other screens."""

    SYMBOL = "symbol"
    ACTION_BUTTON = "action_button"
    EMBEDDED = "embedded"
    NAVTABS = "navtabs"


@dataclass
class WidgetLink:
    """A link from a .bob screen to another screen."""

    file: str  # raw, stripped <file> text
    name: str | None  # widget <name> (or tab <name>)
    type: WidgetType
    macros: dict[str, str]


def extract_file_text(file_elem: ObjectifiedElement) -> str:
    """The stripped text of a <file> element."""
    # Keep raw string to preserve urls
    return file_elem.text.strip() if file_elem.text else ""


def is_bob(file: str) -> bool:
    """Whether the file is a .bob screen."""
    return Path(file).suffix == ".bob"


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
                        continue

                    yield WidgetLink(file, name, widget_type, macros)

                continue

        file = extract_file_text(file_elem)
        # Skip links that are not .bob screens
        if not is_bob(file):
            continue

        yield WidgetLink(file, name, widget_type, macros)


def resolve_link_path(file: str, base_dir: Path, service_name: str) -> Path:
    """Resolve a link's file to a local path."""

    match = PVI_FILE_RE.fullmatch(file)
    # The file path is a PVI screen, so attempt to find that screen
    if match:
        file_name = match.group(1)
        return base_dir / f"../{service_name}/{file_name}"

    return base_dir / file


def find_local_screen(file: str, base_dir: Path, service_name: str) -> Path | None:
    """Resolve a link's file, returning the path if it can be crawled locally."""
    path = resolve_link_path(file, base_dir, service_name)
    return path if path.is_file() else None


def assumed_exists(file: str, macros: Mapping[str, str]) -> bool:
    """Whether a link's file that could not be found locally is assumed to exist."""
    return "IOC" in macros or ("https:/" in file)
