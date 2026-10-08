import logging
from enum import StrEnum

from lxml import objectify
from lxml.etree import Element, SubElement, tostring
from lxml.objectify import ObjectifiedElement, fromstring

logger_ = logging.getLogger(__name__)

__all__ = [
    "WidgetType",
    "get_widgets",
    "read_bob",
    "_get_actions_group",
    "_get_macros",
    "_get_nav_tabs",
]


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

    return tree, widgets


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


def _get_macros(element: ObjectifiedElement):
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
