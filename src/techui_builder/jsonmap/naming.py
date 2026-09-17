"""Display-name rules for ScreenNodes and duplicate-name fixing."""

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from techui_builder.jsonmap.nodes import ScreenNode
from techui_builder.models import Component


def find_techui_label(
    components: Mapping[str, Component],
    component_name: str | None,
    name: str | None,
) -> str | None:
    """The techui.yaml label or child label for a widget name, or None."""
    if name is None:
        return None

    if name in components and components[name].label is not None:
        return components[name].label

    if component_name is None or component_name not in components:
        return None

    child_labels = components[component_name].child_labels
    if child_labels is None:
        return None

    # Because name is initially grabbed from the .bob file, the generated
    # .bob file might have already propagated the child label from techui.yaml
    if name in child_labels.values():
        return name
    # In the case of screens not regenerated, such as validated screens, the name
    # text will not be updated to the child_label, so we check keys solely for
    # generating the json_map from the top level .bob.
    if name in child_labels:
        return child_labels[name]

    return None


def name_or_file_stem(name: str | None, file_path: Path) -> str | None:
    """The name if it is non-empty, else the file name without suffixes, else None."""

    if name:
        # Return name tag text as displayName
        return name

    elif file_path.name:
        # Use tail without file ext as displayName
        return file_path.name[: -sum(len(suffix) for suffix in file_path.suffixes)]

    else:
        # Populate displayName with null
        return None


def fix_duplicate_names(node: ScreenNode) -> None:
    """Recursively fix duplicate display names in children"""
    if not node.children:
        return

    # group by display_name
    name_groups: defaultdict[str | None, list] = defaultdict(list)
    for child in node.children:
        name_groups[child.display_name].append(child)

    # fix duplicates by appending identifiers
    for name, children in name_groups.items():
        if name and len(children) > 1:
            # append pv names when present
            for child in children:
                if "P" in child.macros:
                    child.display_name = f"{name} ({child.macros['P']})"

            # append NO PV NAME and enumeration when there is no pv name
            no_pv_children = [c for c in children if "P" not in c.macros]
            for i, child in enumerate(no_pv_children, 1):
                child.display_name = f"{name} (NO PV NAME {i})"

    # recursively fix children
    for child in node.children:
        fix_duplicate_names(child)
