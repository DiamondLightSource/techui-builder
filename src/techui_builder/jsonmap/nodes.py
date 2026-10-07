"""Data model for the JsonMap screen tree and its JSON serialisation."""

from dataclasses import MISSING, Field, dataclass, field, fields
from typing import Any


@dataclass
class ScreenNode:
    """One screen in the JsonMap tree, with the screens it links to as children."""

    file: str
    display_name: str | None
    exists: bool = True
    children: list["ScreenNode"] = field(default_factory=list)
    macros: dict[str, str] = field(default_factory=dict)
    error: str = ""


def field_default(f: Field[Any]) -> Any:
    """The default value of a dataclass field, or MISSING if it has none."""
    if f.default_factory is not MISSING:
        return f.default_factory()
    return f.default


def serialise_node(node: ScreenNode) -> dict[str, Any]:
    """Convert a ScreenNode and its children to dicts, omitting default values."""
    d = {}
    for f in fields(node):
        value = getattr(node, f.name)
        if value == field_default(f):
            continue
        if f.name == "children":
            value = [serialise_node(child) for child in value]
        d[f.name] = value

    # Rename display_name to displayName for JSON camel case convention
    if "display_name" in d:
        d["displayName"] = d.pop("display_name")

    return d
