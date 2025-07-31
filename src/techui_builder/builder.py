import json
from collections import defaultdict
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import lxml.etree as etree
import yaml

from techui_builder.generate import Generator
from techui_builder.objects import Beamline, Component, Entity

# Recursive type for Json map file
type json_map = MutableMapping[str, str | list["json_map"]]


@dataclass
class Builder:
    """
    This class provides the functionality to process the required
    create_gui.yaml file into screens mapped from ioc.yaml and
    gui_map.yaml files.

    By default it looks for a `create_gui.yaml` file in the same dir
    of the script Guibuilder is called in. Optionally a custom path
    can be declared.

    """

    create_gui: str | Path = field(default=Path("create_gui.yaml"))

    beamline: Beamline = field(init=False)
    components: list[Component] = field(default_factory=list, init=False)
    entities: defaultdict[str, list[Entity]] = field(
        default_factory=lambda: defaultdict(list), init=False
    )
    _services_dir: Path = field(init=False, repr=False)
    _gui_map: dict = field(init=False, repr=False)
    _write_directory: Path = field(init=False, repr=False)

    def __post_init__(self):
        # Populate beamline and components
        self._extract_from_create_gui()

        # Get list of services from the services directory
        # Requires beamline has already been read from create_gui.yaml
        self._services_dir = Path(f"{self.beamline.dom}-services/services")

        self._read_gui_map()

    def _extract_from_create_gui(self):
        """
        Extracts from the create_gui.yaml file to generate
        the required Beamline and components structures.
        """

        with open(self.create_gui) as f:
            conf = yaml.safe_load(f)
            bl: dict[str, str] = conf["beamline"]
            comps: dict[str, dict[str, Any]] = conf[
                "components"
            ]  # TODO: Fix typing from Any

            self.beamline = Beamline(**bl)

            for key, comp in comps.items():
                self.components.append(Component(key, **comp))

    def setup(self):
        """Run intial setup, e.g. extracting entries from service ioc.yaml."""
        self._extract_services()

    def _extract_services(self):
        """
        Finds the services folders in the services directory
        and extracts all entites
        """

        # For each component extracted from create_gui.yaml
        for service in self._services_dir.iterdir():
            # If service doesn't exist, file open will fail throwing exception
            try:
                self._extract_entities(ioc_yaml=service.joinpath("config/ioc.yaml"))
            except OSError:
                print(f"No ioc.yaml file for service: {service.name}. Does it exist?")

    def _extract_entities(self, ioc_yaml: Path):
        """
        Extracts the entries in ioc.yaml matching the defined prefix
        """

        with open(ioc_yaml) as ioc:
            ioc_conf: dict[str, list[dict[str, str]]] = yaml.safe_load(ioc)
            for entity in ioc_conf["entities"]:
                if "P" in entity.keys():
                    # Create Entity and append to entity list
                    new_entity = Entity(
                        type=entity["type"],
                        desc=entity.get("desc", None),
                        P=entity["P"],
                        M=None
                        if (val := entity.get("M")) is None
                        else val.removeprefix(":"),
                        R=None
                        if (val := entity.get("R")) is None
                        else val.removeprefix(":"),
                    )
                    self.entities[new_entity.P].append(new_entity)

    def _read_gui_map(self):
        """Read the gui_map.yaml file from techui-support."""
        gui_map = Path("./techui-support/gui_map.yaml")

        with open(gui_map) as map:
            self._gui_map = yaml.safe_load(map)

    def _generate_screen(self, screen_name: str, screen_components: list[Entity]):
        generator = Generator(screen_components, self._gui_map, screen_name)
        generator.build_groups()
        generator.write_screen(self._write_directory)

    def generate_screens(self):
        """Generate the screens for each component in create_gui.yaml"""
        if self.entities is None:
            raise Exception("No entities found, has setup() been run?")

        # Loop over every component defined in create_gui.yaml and locate
        # any extras defined
        for component in self.components:
            screen_entities: list[Entity] = []
            # ONLY IF there is a matching component and entity, generate a screen
            if component.prefix in self.entities.keys():
                screen_entities.extend(self.entities[component.prefix])
                if component.extras is not None:
                    # If component has any extras, add them to the entries to generate
                    for extra_p in component.extras:
                        screen_entities.extend(self.entities[extra_p])

                self._generate_screen(component.name, screen_entities)

    def _generate_json_map(
        self, file_path: Path, visited: set[Path] | None = None
    ) -> json_map:
        if visited is None:
            visited = set()

        abs_path = file_path.absolute()
        if abs_path in visited:
            return {"file": str(file_path), "note": "Already visited (cycle detected)"}

        visited.add(abs_path)
        node: json_map = {"file": str(file_path), "children": []}

        try:
            tree = etree.parse(abs_path, None)
            root: etree._ElementTree = tree.getroot()

            # Find all <file> elements
            for file_elem in root.findall(".//file", namespaces=None):
                file_elem: etree._Element
                # Extract file path from file_elem
                file_path = Path(file_elem.text.strip() if file_elem.text else "")
                # If file is already a .bob file, skip it
                if not file_path.suffix == ".bob":
                    continue

                # TODO: misleading var name?
                next_file_path = abs_path.joinpath(file_path)

                # Obtain macros associated with file_elem
                macro_dict: dict[str, str] = {}
                widget: etree._Element = file_elem.getparent()
                if widget is not None:
                    macros: etree._Element = widget.find("macros", namespaces=None)
                    if macros is not None:
                        p: etree._Element = macros.find(".//P", namespaces=None)
                        m: etree._Element = macros.find(".//M", namespaces=None)
                        if p is not None and p.text:
                            macro_dict["P"] = p.text
                        if m is not None and m.text:
                            macro_dict["M"] = m.text

                # Crawl the next file
                if next_file_path.is_file():
                    # TODO: investigate non-recursive approaches?
                    next_node = self._generate_json_map(next_file_path, visited)
                else:
                    next_node = {"file": str(file_path), "error": "File not found"}

                next_node.update(macro_dict)
                # TODO: make this work for only list[json_map]
                assert isinstance(node["children"], list)
                # TODO: fix typing
                node["children"].append(next_node)  # type: ignore

        except etree.ParseError as e:
            node["error"] = f"XML parse error: {e}"
        except Exception as e:
            node["error"] = str(e)

        # Write json map to file
        with open("map.json", "w") as outfile:
            json.dump(node, outfile)

        return node

    # TODO: change default Path
    def get_json_map(self, file_name: Path = Path("motor.bob")):
        """
        Maps the valid entries from the ioc.yaml file
        to the required screen in gui_map.yaml
        """
        map = self._generate_json_map(file_name)
        print(map)
