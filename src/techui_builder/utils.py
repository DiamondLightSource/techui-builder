import logging
from pathlib import Path

from lxml import objectify
from lxml.objectify import ObjectifiedElement

logger_ = logging.getLogger(__name__)


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
                case "action_button" | "symbol":
                    name = child.name.text
                    assert name is not None
                    widgets[name] = child
                case "group":
                    # Get all the widgets inside of the group objects
                    groups_widgets = get_widgets(child)
                    widgets.update(groups_widgets)
                case "navtabs":
                    # There is a switch to toggle between screens
                    # e.g. for different hutches on the main index.bob
                    # so we need to extract those files and the widgets
                    # on them.
                    tabs = _get_nav_tabs(child)

                    if tabs is None:
                        continue

                    for tab in tabs:
                        # name_elem = tab.name.text
                        file_elem = tab.file
                        # macro_dict = _get_macros(tab)

                        # Extract file path from file_elem
                        # Keep raw string to preserve urls
                        file_text = file_elem.text.strip() if file_elem.text else ""
                        file_path = Path(file_text)

                        # If file is already a .bob file, skip it
                        if not file_path.suffix == ".bob":
                            continue

                        assert root.base, (
                            f"The file path for the screen is invalid: {root.base}"
                        )
                        root_file_dir = Path(root.base).parent

                        # try to find the navtab screen next to the parent screen
                        sub_screen_path = root_file_dir / file_path
                        assert sub_screen_path.exists(), (
                            f"The navtab screen '{file_path}' does not exist next to"
                            f" name {Path(root.base).name}"
                        )

                        _, sub_widgets = read_bob(sub_screen_path)
                        widgets.update(sub_widgets)

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
def _get_action_group(element: ObjectifiedElement) -> ObjectifiedElement | None:
    try:
        actions = element.actions
        assert actions is not None
        for action in actions.iterchildren("action"):
            if action.get("type", default=None) == "open_display":
                return action
        return None
    except AttributeError:
        # TODO: Find better way of handling there being no "actions" group
        # TODO: Do widgets always have a name attr, or _can_ it be empty??
        name = element.name

        parent_name = p.name if (p := element.getparent()) is not None else None

        logger_.error(
            f"Actions group not found in component [bold]{name}[/bold] on "
            f"[bold]{parent_name}[/bold]"
        )


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
