import logging
import re
from enum import StrEnum

from lxml import objectify
from lxml.etree import Element, SubElement, tostring
from lxml.objectify import ObjectifiedElement, fromstring

from techui_builder.models import RawMacroMap

logger_ = logging.getLogger(__name__)

__all__ = [
    "WidgetType",
    "get_widgets",
    "read_bob",
    "_get_actions_group",
    "_get_macros",
    "_get_nav_tabs",
    "_INDEX_BOB_NAME_RE",
]

# index_bob_name_pattern = r"{?(\w+)\s*=\s*(\[.*?\]|.*?)(?=\s*,\s*\w+\s*=|\s*}$)"

_INDEX_BOB_NAME_PATTERN_VERBOSE = r"""
    (?:^{)?                 # optional '{' at the start of the string (the ^ only
                            # anchors the '{')

    (?!.*\s,)               # LOOKAHEAD 1 (negative): no whitespace directly before a
                            # comma later on the line
    (?!\]*\s)               # LOOKAHEAD 2 (negative): fail on whitespace here, or ']'s
                            # then whitespace

    (?:                     # start of alternation

        (?:([\w]+))         # GROUP 1: the key, one or more word chars
        \s?=\s?             # '=' with at most one space either side

        (?=[\w\s:\-.]+)     # LOOKAHEAD A (positive): at least one "value char" must
                            # come next
                            #   (value char = [\w\s:\-.] = word char, whitespace, ':',
                            # '-' or '.')
    |                       # OR
        (?=\[?[\w\s:\-.]+(?:,\s?)?\]?)
                            # LOOKAHEAD B (positive): an optional '[', value chars, an
                            # optional ',' + one space and an optional ']' must come
                            # next (never changes the result)

        (?:(?:
            ([\w\s:\-.]+)   # GROUP 2: a bare value, one or more value chars
            (?:,\s?)?       # optional trailing comma (consumed, not captured)
        ))

    |                       # OR
        (                   # GROUP 3: a bracketed list, e.g. "[a, b, c]"
            \[              #   literal '['
            (?:
                (?:[\w\s:\-.]+)   #   an item: one or more value chars
                (?:,\s?)?         #   optional comma
            )*              #   zero or more items
            \]              #   literal ']'
        )
    )                       # end of alternation

    (?:}$)?                 # optional '}' at the end of the string
    """

_INDEX_BOB_NAME_RE = re.compile(_INDEX_BOB_NAME_PATTERN_VERBOSE, re.VERBOSE)


class WidgetType(StrEnum):
    """Widget types in a .bob file."""

    ACTION_BUTTON = "action_button"
    EMBEDDED = "embedded"
    GROUP = "group"
    NAVTABS = "navtabs"
    SYMBOL = "symbol"


def read_bob(path):
    # Read the bob file
    tree = objectify.parse(path)

    # Find the root tag (in this case: <display version="2.0.0">)
    root = tree.getroot()

    widgets = get_widgets(root)

    macros = _get_macros(root)

    return tree, widgets, macros


def get_widgets(root: ObjectifiedElement):
    widgets: dict[str, ObjectifiedElement] = {}
    # Loop over objects in the xml
    # i.e. every tag below <display version="2.0.0">
    # but not any nested tags below them
    for child in root.iterchildren():
        # If widget is a symbol (i.e. a component)
        if child.tag == "widget":
            match child.get("type", default=None):
                case WidgetType.ACTION_BUTTON | WidgetType.SYMBOL | WidgetType.NAVTABS:
                    name = child.name.text
                    assert name is not None
                    widgets[name] = child
                case WidgetType.GROUP:
                    # Get all the widgets inside of the group objects
                    groups_widgets = get_widgets(child)
                    widgets.update(groups_widgets)

    return widgets


def _get_macros(element: ObjectifiedElement) -> RawMacroMap:
    if hasattr(element, "macros"):
        macros = element.macros.getchildren()
        if macros is not None:
            return {
                str(macro.tag): macro.text for macro in macros if macro.text is not None
            }
    return {}


# File and desc are under the "actions",
# so the corresponding tag needs to be found
def _get_actions_group(element: ObjectifiedElement) -> ObjectifiedElement | None:
    try:
        actions = element.actions
        assert actions is not None
        return actions

    except AttributeError:
        # TODO: Find better way of handling there being no "actions" group
        # TODO: Do widgets always have a name attr, or _can_ it be empty??
        name = element.name

        parent_name = p.name if (p := element.getparent()) is not None else None

        logger_.error(
            f"Actions group not found in component [bold]{name}[/bold] on "
            f"[bold]{parent_name}[/bold]"
        )
        return None


# File and desc are under the "actions",
# so the corresponding tag needs to be found
def _get_open_display_action(element: ObjectifiedElement) -> ObjectifiedElement:
    actions = _get_actions_group(element)

    if actions is not None:
        for action in actions.iterchildren("action"):
            if action.get("type", default=None) == "open_display":
                return action

    # No open_display action found, add one
    return _add_open_display(element)


def _add_open_display(element: ObjectifiedElement) -> ObjectifiedElement:
    if _get_actions_group(element) is None:
        # This is the objectify SubElement so needs to be explicit
        actions = objectify.SubElement(element, "actions")
    else:
        actions = element.actions

    action = Element("action")
    action.set("type", "open_display")
    file = SubElement(action, "file")
    file.text = "placeholder_file"
    desc = SubElement(action, "description")
    desc.text = "placeholder_desc"
    target = SubElement(action, "target")
    target.text = "tab"

    action_element = fromstring(tostring(action))
    actions.append(action_element)
    return action_element


def _get_nav_tabs(element: ObjectifiedElement) -> list[ObjectifiedElement] | None:
    try:
        element_tabs = element.tabs
        assert element_tabs is not None

        tabs = list(element_tabs.iterchildren("tab"))

        return tabs

    except AttributeError:
        # TODO: Find better way of handling there being no "tabs" group
        # TODO: Do widgets always have a name attr, or _can_ it be empty??
        name = element.name

        parent_name = p.name if (p := element.getparent()) is not None else None

        logger_.error(
            f"Tabs group not found in component [bold]{name}[/bold] on "
            f"[bold]{parent_name}[/bold]"
        )
