from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree, objectify  # type: ignore

from techui_builder.builder import Builder
from techui_builder.objects import Component


@dataclass
class Autofiller:
    path: Path
    macros: list[str] = field(default_factory=lambda: ["prefix", "desc", "file"])

    def read_bob(self) -> None:
        parser = etree.XMLParser()
        # Read the bob file
        self.tree: etree._ElementTree = objectify.parse(self.path, parser)

        # Find the root tag (in this case: <display version="2.0.0">)
        self.root = self.tree.getroot()

    def autofill_bob(self, gui: "Builder"):
        # Get names from component list
        comp_names = [comp.name for comp in gui.components]

        # Loop over objects in the xml
        # i.e. every tag below <display version="2.0.0">
        # but not any nested tags below them
        for child in self.root:
            # For type hinting
            assert isinstance(child, etree._Element)  # noqa: SLF001

            # If widget is a symbol (i.e. a component)
            if child.tag == "widget" and child.get("type", default=None) == "symbol":
                # Extract it's name
                symbol_name = child.find("name", namespaces=None).text

                # If the name exists in the component list
                if symbol_name in comp_names:
                    # Get first copy of component (should only be one)
                    comp = next(
                        (comp for comp in gui.components if comp.name == symbol_name),
                    )

                    self.replace_macros(widget=child, component=comp)

    def write_bob(self, filename: Path):
        self.tree.write(
            filename,
            pretty_print=True,  # type: ignore
            encoding="utf-8",  # type: ignore
            xml_declaration=True,  # type: ignore
        )

    def _sub_macro(
        self, tag_name: str, macro: str, element: etree._Element, current_macro: str
    ) -> None:
        # Extract it's current tag text, or if empty set to $(<macro>)
        old: str = element.find(tag_name, namespaces=None).text or f"$({macro})"

        # Replace instance of {<macro>} with the component's corresponding attribute
        new: str = old.replace(f"$({macro})", current_macro)

        # Set component's tag text to the autofilled macro
        element.find(tag_name, namespaces=None).text = new

    def replace_macros(self, widget: etree._Element, component: Component):
        # File and desc are under the "actions",
        # so the corresponding tag needs to be found
        def _get_action_group(element: etree._Element) -> etree._Element:
            actions: etree._Element = element.find("actions", namespaces=None)
            for action in actions.iterchildren("action"):
                if action.get("type", default=None) == "open_display":
                    return action

            # TODO: Find better way of handling there being no "actions" group
            raise Exception(f"Actions group not found in component: {component.name}")

        for macro in self.macros:
            # Get current component attribute
            component_attr = getattr(component, f"{macro}")
            # If it is None, then it was not provided so ignore
            if component_attr is None:
                continue

            # Fix to make sure widget is reverted back to widget that was passed in
            current_widget = widget
            match macro:
                case "prefix":
                    tag_name = "pv_name"
                case "desc":
                    tag_name = "description"
                    current_widget = _get_action_group(widget)
                case "file":
                    tag_name = "file"
                    current_widget = _get_action_group(widget)
                case _:
                    raise ValueError("The provided macro type is not supported.")

            self._sub_macro(
                tag_name=tag_name,
                macro=macro,
                element=current_widget,
                current_macro=component_attr,
            )
