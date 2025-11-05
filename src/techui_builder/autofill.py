import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from lxml import objectify
from lxml.objectify import ObjectifiedElement

from techui_builder.builder import Builder, _get_action_group
from techui_builder.models import Component

LOGGER = logging.getLogger(__name__)


@dataclass
class Autofiller:
    path: Path
    macros: list[str] = field(default_factory=lambda: ["prefix", "desc", "file"])

    def read_bob(self) -> None:
        # Read the bob file
        self.tree = objectify.parse(self.path)

        # Find the root tag (in this case: <display version="2.0.0">)
        self.root = self.tree.getroot()

    def autofill_bob(self, gui: "Builder"):
        # Get names from component list

        # Loop over objects in the xml
        # i.e. every tag below <display version="2.0.0">
        # but not any nested tags below them
        for child in self.root.iterchildren():
            # If widget is a symbol (i.e. a component)
            if child.tag == "widget" and child.get("type", default=None) == "symbol":
                # Extract it's name
                symbol_name = child.name

                # If the name exists in the component list
                if symbol_name in gui.conf.components.keys():
                    # Get first copy of component (should only be one)
                    comp = next(
                        (comp for comp in gui.conf.components if comp == symbol_name),
                    )

                    self.replace_macros(
                        widget=child,
                        component_name=comp,
                        component=gui.conf.components[comp],
                    )

    def write_bob(self, filename: Path):
        # Check if data/ dir exists and if not, make it
        data_dir = filename.parent
        if not data_dir.exists():
            os.mkdir(data_dir)

        self.tree.write(
            filename,
            pretty_print=True,  # type: ignore
            encoding="utf-8",  # type: ignore
            xml_declaration=True,  # type: ignore
        )
        LOGGER.debug(f"Screen filled for {filename}")

    def _sub_macro(
        self,
        tag_name: str,
        macro: str,
        element: ObjectifiedElement,
        current_macro: str,
    ) -> None:
        # Extract it's current tag text, or if empty set to $(<macro>)
        old: str = (
            el.text
            if (el := element.find(tag_name)) is not None and el.text is not None
            else f"$({macro})"
        )

        # Replace instance of {<macro>} with the component's corresponding attribute
        new: str = old.replace(f"$({macro})", current_macro)

        # Set component's tag text to the autofilled macro
        element[tag_name] = new

    def replace_macros(
        self,
        widget: ObjectifiedElement,
        component_name: str,
        component: Component,
    ):
        for macro in self.macros:
            # Get current component attribute
            component_attr = getattr(component, macro)
            # If it is None, then it was not provided so ignore
            if component_attr is None and macro != "desc":
                continue

            # Fix to make sure widget is reverted back to widget that was passed in
            current_widget = widget
            match macro:
                case "prefix":
                    tag_name = "pv_name"
                case "desc":
                    tag_name = "description"
                    current_widget = _get_action_group(widget)
                    if component_attr is None:
                        component_attr = component_name
                case "file":
                    tag_name = "file"
                    current_widget = _get_action_group(widget)
                case _:
                    raise ValueError("The provided macro type is not supported.")

            if current_widget is None:
                LOGGER.debug(
                    f"Skipping replace_macros for {component_name} as no action\
 group found"
                )
                continue

            self._sub_macro(
                tag_name=tag_name,
                macro=macro,
                element=current_widget,
                current_macro=component_attr,
            )
