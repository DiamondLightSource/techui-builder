import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from lxml import objectify
from lxml.objectify import ObjectifiedElement

from techui_builder.builder import Builder, _get_action_group
from techui_builder.models import Component
from techui_builder.utils import read_bob

logger_ = logging.getLogger(__name__)


@dataclass
class Autofiller:
    path: Path
    macros: list[str] = field(default_factory=lambda: ["prefix", "desc", "file"])
    widgets: dict[str, ObjectifiedElement] = field(
        default_factory=defaultdict, init=False, repr=False
    )

    def read_bob(self) -> None:
        self.tree, self.widgets = read_bob(self.path)

    def autofill_bob(self, gui: "Builder"):
        # Get names from component list

        for symbol_name, child in self.widgets.items():
            # If the name exists in the component list
            if symbol_name in gui.conf.components.keys():
                # Get first copy of component (should only be one)
                comp = next(
                    (comp for comp in gui.conf.components if comp == symbol_name),
                )

                self.replace_content(
                    widget=child,
                    component_name=comp,
                    component=gui.conf.components[comp],
                )

                # Add option to allow left mouse click to run action
                child["run_actions_on_mouse_click"] = "true"

    def write_bob(self, filename: Path):
        # Check if data/ dir exists and if not, make it
        data_dir = filename.parent
        if not data_dir.exists():
            os.mkdir(data_dir)

        # Remove any unnecessary xmlns:py and py:pytype metadata from tags
        objectify.deannotate(self.tree, cleanup_namespaces=True)

        self.tree.write(
            filename,
            pretty_print=True,
            encoding="utf-8",
            xml_declaration=True,
        )
        logger_.debug(f"Screen filled for {filename}")

    def replace_content(
        self,
        widget: ObjectifiedElement,
        component_name: str,
        component: Component,
    ):
        for macro in self.macros:
            # Get current component attribute
            component_attr = getattr(component, macro)

            # Fix to make sure widget is reverted back to widget that was passed in
            current_widget = widget
            match macro:
                case "prefix":
                    tag_name = "pv_name"
                    component_attr += ":DEVSTA"
                case "desc":
                    tag_name = "description"
                    current_widget = _get_action_group(widget)
                    if component_attr is None:
                        component_attr = component_name
                case "file":
                    tag_name = "file"
                    current_widget = _get_action_group(widget)
                    if component_attr is None:
                        component_attr = f"{component_name}.bob"
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
