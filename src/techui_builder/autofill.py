import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from lxml import objectify
from lxml.etree import Element, ElementTree, SubElement, tostring
from lxml.objectify import ObjectifiedElement, fromstring

from techui_builder.models import Component
from techui_builder.utils import _get_action_group, _get_nav_tabs, read_bob

logger_ = logging.getLogger(__name__)

WidgetDict = dict[str, ObjectifiedElement]
TreeWidgetDictTuple = tuple[ElementTree, WidgetDict]
IndexObjectDict = dict[Path, TreeWidgetDictTuple]


@dataclass
class Autofiller:
    index_paths: list[Path]
    base_index_path: Path
    gui_components: dict[str, Component]
    macros: list[str] = field(
        default_factory=lambda: ["prefix", "desc", "file", "macros"]
    )
    index_trees: IndexObjectDict = field(default_factory=dict, init=False, repr=False)

    def read_bobs(self) -> None:
        for path in self.index_paths:
            tree, widget_dict = read_bob(path)
            self.index_trees[path] = (tree, widget_dict)

    def autofill_bobs(self) -> None:
        self._autofill_from_path(self.base_index_path)

    def _autofill_from_path(self, path: Path):
        tree, widgets = self.index_trees[path]

        logger_.debug(f"Autofilling screen: {path.name}")

        for widget_name, widget in widgets.items():
            match widget.get("type", default=None):
                case "navtabs":
                    logger_.debug(
                        f"Navtabs widget found on {path.name}. Autofilling the tabs..."
                    )
                    tabs = _get_nav_tabs(widget)
                    if tabs is not None:
                        for tab in tabs:
                            if tab.file.text is None:
                                continue
                            file_path = Path(tab.file.text)
                            if file_path.suffix != ".bob":
                                continue
                            root = tree.getroot()
                            if root.base is None:
                                continue
                            root_dir = Path(root.base).parent
                            resolved_path = root_dir / file_path
                            if resolved_path in self.index_trees:
                                self._autofill_from_path(resolved_path)
                            else:
                                if resolved_path.exists():
                                    nav_tree, nav_widgets = read_bob(resolved_path)
                                    self.index_trees[resolved_path] = (
                                        nav_tree,
                                        nav_widgets,
                                    )
                                self._autofill_from_path(resolved_path)
                case _:
                    if widget_name in self.gui_components:
                        self.replace_content(
                            widget=widget,
                            component_name=widget_name,
                            component=self.gui_components[widget_name],
                        )
                        widget["run_actions_on_mouse_click"] = "true"

    def _write_bob(self, path: Path, tree: ElementTree) -> None:
        # tree, _ = self.index_trees[path]
        # Check if data/ dir exists and if not, make it
        data_dir = path.parent
        if not data_dir.exists():
            os.mkdir(data_dir)

        # Remove any unnecessary xmlns:py and py:pytype metadata from tags
        objectify.deannotate(tree, cleanup_namespaces=True)

        tree.write(
            path,
            pretty_print=True,
            encoding="utf-8",
            xml_declaration=True,
        )
        logger_.debug(f"Screen filled for {path}")

    def write_bobs(self) -> None:
        for path, (tree, _) in self.index_trees.items():
            self._write_bob(path, tree)

    def replace_content(
        self,
        widget: ObjectifiedElement,
        component_name: str,
        component: Component,
    ):
        for macro in self.macros:
            # Fix to make sure widget is reverted back to widget that was passed in
            current_widget = widget

            match macro:
                case "prefix":
                    tag_name = "pv_name"
                    component_attr = f"{component.P}:STA"

                case "desc" | "file" | "macros":
                    # Get current component attribute
                    component_attr = getattr(component, macro, None)

                    current_widget = _get_action_group(widget)
                    match macro:
                        case "desc":
                            tag_name = "description"

                            if component_attr is None:
                                component_attr = (
                                    component_name
                                    if component.label is None
                                    else component.label
                                )

                        case "file":
                            tag_name = "file"

                            if component_attr is None:
                                component_attr = f"{component_name}.bob"

                        case "macros":
                            tag_name = "macros"

                            if component_attr is None:
                                # If no custom macros are provided, don't run this code
                                # As this will overwrite generated macros
                                continue

                            assert current_widget is not None
                            # Remove all existing macros if they exist
                            if hasattr(current_widget, "macros"):
                                current_widget.remove(current_widget.macros)
                            # Create new macros element
                            current_widget.append(
                                self._create_macro_element(component_attr)
                            )
                            # Break out of the loop
                            continue

                case _:
                    raise ValueError("The provided macro type is not supported.")

            if current_widget is None:
                logger_.debug(
                    f"Skipping replace_content for {component_name} as no action\
 group found"
                )
                continue

            # Set component's tag text to the corresponding widget tag
            current_widget[tag_name] = component_attr

    def _create_macro_element(self, macros: dict):
        # You cannot set a text tag of an ObjectifiedElement,
        # so we need to make an etree.Element and convert it ...

        macros_element = Element("macros")
        for macro, val in macros.items():
            macro_element = SubElement(macros_element, macro)
            macro_element.text = str(val)

        # ... which requires this horror
        obj_macros_element = fromstring(tostring(macros_element))

        return obj_macros_element
