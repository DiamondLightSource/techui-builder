"""Recursively crawl a tree of .bob screens into a tree of ScreenNodes."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from lxml import etree, objectify
from lxml.objectify import ObjectifiedElement

from techui_builder.jsonmap.links import (
    WidgetLink,
    WidgetType,
    assumed_exists,
    extract_links,
    find_local_screen,
)
from techui_builder.jsonmap.naming import (
    find_techui_label,
    fix_duplicate_names,
    name_or_file_stem,
)
from techui_builder.jsonmap.nodes import ScreenNode
from techui_builder.models import Component


@dataclass
class CrawlContext:
    """State passed down the recursion."""

    components: Mapping[str, Component]
    synoptic_dir: Path  # ScreenNode.file is relative to this
    link_base_dir: Path  # link files are resolved against this; never changes
    component_name: str | None
    service_name: str

    def with_screen_component(self, screen_path: Path) -> "CrawlContext":
        """A copy for the screen's component, if it is one and none is set yet."""
        if self.component_name is not None or screen_path.stem not in self.components:
            return self

        component_name = screen_path.stem
        # We know from the if statement that it exists
        component = self.components.get(component_name)
        assert isinstance(component, Component)
        # TODO: How to find the screens if PV prefix is not the service name???
        return replace(
            self, component_name=component_name, service_name=component.prefix.lower()
        )


def crawl_link(
    link: WidgetLink, display_name: str | None, ctx: CrawlContext
) -> ScreenNode:
    """
    Determine if the child node file exists, and if it does, recursively
    generate a ScreenNode for it and its children.

    If it can't be found, a leaf ScreenNode is returned.
    """
    local_path = find_local_screen(link.file, ctx.link_base_dir, ctx.service_name)

    # Crawl the next file
    if local_path is not None:
        # TODO: investigate non-recursive approaches?
        return crawl(local_path, ctx, link_name=link.name)

    return ScreenNode(
        link.file,
        display_name,
        exists=assumed_exists(link.file, link.macros),
    )


def crawl(
    screen_path: Path, ctx: CrawlContext, link_name: str | None = None
) -> ScreenNode:
    """Crawl a .bob screen and the screens it links to into a ScreenNode."""

    # Create initial node at top of .bob file
    current_node = ScreenNode(
        str(
            screen_path.resolve().relative_to(ctx.synoptic_dir.resolve(), walk_up=True)
        ),
        display_name=None,
    )

    ctx = ctx.with_screen_component(screen_path)

    try:
        # Create xml tree from .bob file
        tree = objectify.parse(screen_path.absolute())
        root: ObjectifiedElement = tree.getroot()

        # Label for the linking widget, else the screen's own <name>, else file stem
        own_name = name_or_file_stem(root.name.text, screen_path)
        label = find_techui_label(ctx.components, ctx.component_name, link_name)
        current_node.display_name = label if label is not None else own_name

        for link in extract_links(root):
            # Label, else widget <name>, else file stem
            label = find_techui_label(ctx.components, ctx.component_name, link.name)
            display_name = name_or_file_stem(
                label if label is not None else link.name, Path(link.file)
            )

            child_node = crawl_link(link, display_name, ctx)

            if link.type == WidgetType.EMBEDDED:
                for embedded_child in child_node.children:
                    embedded_child.macros = {**embedded_child.macros, **link.macros}
                    embedded_child.display_name = display_name
                    embedded_child.exists = "IOC" in link.macros or (
                        "https://" in str(embedded_child.file)
                    )
                    current_node.children.append(embedded_child)

            else:
                child_node.macros = link.macros
                # TODO: make this work for only list[ScreenNode]
                assert isinstance(current_node.children, list)
                # TODO: fix typing
                current_node.children.append(child_node)

    except etree.ParseError as e:
        current_node.error = f"XML parse error: {e}"
    except Exception as e:
        current_node.error = str(e)

    fix_duplicate_names(current_node)

    return current_node
