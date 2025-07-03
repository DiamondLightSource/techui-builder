from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree, objectify

from techui_builder.builder import Builder
from techui_builder.datatypes import Component


@dataclass
class BobScreen:
    path: Path
    macros: list[str] = field(
        default=["prefix", "desc", "bob_file"],
    )

    # def __init__(self, bob_path: str | Path):
    #     bob_path = bob_path if isinstance(bob_path, Path) else Path(bob_path)

    #     assert bob_path.exists(), warnings.warn(
    #         f"Bob file {bob_path} can't be found. Does it exist?", stacklevel=1
    #     )

    #     self.path = bob_path

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

                    self.replace_macro(widget=child, component=comp)

    def write_bob(self, filename: Path):
        self.tree.write(
            filename,
            pretty_print=True,  # type: ignore
            encoding="utf-8",  # type: ignore
            xml_declaration=True,  # type: ignore
        )

    def _sub_macro(
        self, tag_name: str, macro: str, element: etree._Element, comp: Component
    ) -> None:
        # Extract it's current tag text, or if empty set to $(<macro>)
        old: str = element.find(tag_name, namespaces=None).text or f"$({macro})"

        # Replace instance of {<macro>} with the component's corresponding attribute
        new: str = old.replace(f"$({macro})", getattr(comp, f"{macro}"))

        # Set component's tag text to the autofilled macro
        element.find(tag_name, namespaces=None).text = new

    def replace_macro(self, widget: etree._Element, component: Component):
        for macro in self.macros:
            match macro:
                case "prefix":
                    tag_name = "pv_name"
                case "desc":
                    tag_name = "description"
                case "bob_file":
                    # actions: etree._Element = element.find("actions", namespaces=None)
                    # for action in actions.iterchildren("action"):
                    #     if action.get("type", default=None) == "open_display":
                    #         ...
                    tag_name = "file"
                case _:
                    raise ValueError("The provided macro type is not supported.")

            self._sub_macro(tag_name, macro, widget, component)
