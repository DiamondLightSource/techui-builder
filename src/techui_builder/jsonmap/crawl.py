"""Recursively crawl a tree of .bob screens into a tree of ScreenNodes."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from lxml import etree, objectify

from techui_builder.jsonmap.links import (
    WidgetLink,
    extract_links,
    resolve_link,
    substitute_macros,
)
from techui_builder.jsonmap.naming import (
    find_techui_label,
    fix_duplicate_names,
    name_or_file_stem,
)
from techui_builder.jsonmap.nodes import ScreenNode
from techui_builder.models import Component
from techui_builder.utils import WidgetType

logger_ = logging.getLogger(__name__)


@dataclass
class CrawlContext:
    """State passed down the recursion."""

    components: Mapping[str, Component]
    synoptic_dir: Path  # ScreenNode.file is relative to this
    component_name: str | None
    screen: Path  # the screen being crawled
    macros: dict[str, str] = field(default_factory=dict)  # including inherited ones

    def with_screen(self, screen: Path) -> "CrawlContext":
        """A copy for crawling a screen's links, in its component if it names one."""
        component_name = self.component_name
        if component_name is None and screen.stem in self.components:
            component_name = screen.stem

        return replace(self, screen=screen, component_name=component_name)


def format_screen(screen: Path, synoptic_dir: Path) -> str:
    """The screen's path, relative to the synoptic directory."""
    return str(screen.resolve().relative_to(synoptic_dir.resolve(), walk_up=True))


def inherit_macros(
    parent_macros: Mapping[str, str], macros: Mapping[str, str]
) -> dict[str, str]:
    """The parent's macros overridden by a link's macros, expanded like Phoebus."""
    expanded = {k: substitute_macros(v, parent_macros) for k, v in macros.items()}
    return {**parent_macros, **expanded}


def crawl_link(
    link: WidgetLink, display_name: str | None, ctx: CrawlContext
) -> ScreenNode:
    """
    Determine if the child node file exists, and if it does, recursively
    generate a ScreenNode for it and its children.

    If it can't be found, a leaf ScreenNode is returned.
    """
    macros = inherit_macros(ctx.macros, link.macros)
    screen = resolve_link(link.file, macros, ctx.screen)

    if not screen.is_file():
        logger_.debug(f"Link {link.file} -> {screen}: not found")
        return ScreenNode(
            format_screen(screen, ctx.synoptic_dir),
            display_name,
            exists=False,
            macros=macros,
        )

    logger_.debug(f"Link {link.file} -> {screen}: found")

    # Crawl the next file
    # TODO: investigate non-recursive approaches?
    node = crawl(screen, replace(ctx, macros=macros), link_name=link.name)
    node.macros = macros
    return node


def crawl(screen: Path, ctx: CrawlContext, link_name: str | None = None) -> ScreenNode:
    """Crawl a .bob screen and the screens it links to into a ScreenNode."""

    # Create initial node at top of .bob file
    current_node = ScreenNode(
        format_screen(screen, ctx.synoptic_dir), display_name=None
    )

    ctx = ctx.with_screen(screen)

    try:
        # Create xml tree from .bob file
        root = objectify.parse(screen.absolute()).getroot()

        # Label for the linking widget, else the screen's own <name>, else file stem
        own_name = name_or_file_stem(root.name.text, screen)
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
                    embedded_child.display_name = display_name
                    current_node.children.append(embedded_child)

            else:
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
