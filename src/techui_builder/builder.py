import json
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from pathlib import Path

import lxml.etree as etree
import yaml

from techui_builder.generate import Generator
from techui_builder.objects import Beamline, Component, Entry

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

    components: list[Component] = field(default_factory=list, init=False)
    entities: list[Entry] = field(default_factory=list, init=False)
    beamline: Beamline = field(init=False)

    def setup(self):
        """Run intial setup, e.g. extracting components from create_gui.yaml."""
        self._extract_from_create_gui()
        self._find_services_folders()
        # self._read_gui_map()

    def _extract_from_create_gui(self):
        """
        Extracts from the create_gui.yaml file to generate
        the required Beamline and components structures.
        """

        with open(self.create_gui) as f:
            conf = yaml.safe_load(f)
            bl: dict[str, str] = conf["beamline"]
            comps: dict[str, dict[str, str]] = conf["components"]

            self.beamline = Beamline(**bl)

            for key, comp in comps.items():
                self.components.append(Component(key, **comp))

    def _find_services_folders(self):
        """
        Finds the related folders in the services directory
        and extracts the related entites with the matching prefixes
        """

        # Get list of services from services_directory
        services_directory = (
            "./example/" + self.beamline.dom + "-services/services"
        )  # TODO: rm hardcoding, map to services.
        path = f"{services_directory}"

        # For each component extracted from create_gui.yaml
        for component in self.components:
            if component.service_name is not None:
                service_name = component.service_name
            else:
                # if service_name is not provided, resort to P being the service name
                service_name = component.P.lower()

            # If service doesn't exist, file open will fail throwing exception
            try:
                self._extract_entities(
                    ioc_yaml=f"{path}/{service_name}/config/ioc.yaml",
                    component=component,
                )
                self._read_gui_map()
                self.entities = []
            except OSError:
                print(f"No ioc.yaml file for service: {service_name}. Does it exist?")

    def _extract_entities(self, ioc_yaml: str, component: Component):
        """
        Extracts the entities in ioc.yaml matching the defined prefix
        """

        with open(ioc_yaml) as ioc:
            conf: dict[str, list[dict[str, str]]] = yaml.safe_load(ioc)
            for entity in conf["entities"]:
                if (
                    "P" in entity.keys()
                    # TODO: think about multiple prefixes per service e.g. i19 DIFF1S
                    ### and entity["P"] == component.prefix
                ):
                    # Create Entry and append to entity list
                    entry = Entry(
                        type=entity["type"],
                        desc=component.desc,
                        # TODO: Implement gui_map screen path
                        file=Path(component.name + ".bob")
                        if component.file is None
                        else Path(component.file),
                        P=entity["P"],
                        M=None
                        if (val := entity.get("M")) is None
                        else val.removeprefix(":"),
                        R=None
                        if (val := entity.get("R")) is None
                        else val.removeprefix(":"),
                    )
                    self.entities.append(entry)

    def _read_gui_map(self):
        """Read the gui_map.yaml file from techui-support."""
        gui_map = "./techui-support/gui_map.yaml"

        with open(gui_map) as map:
            conf = yaml.safe_load(map)
            # TODO: Why is this here? It doesn't seem like it is doing anything
            generator = Generator(self.entities, conf)
            generator.build_groups()
            generator.write_screen()
            self.gui_map = conf

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
        Maps the valid entities from the ioc.yaml file
        to the required screen in gui_map.yaml
        """
        map = self._generate_json_map(file_name)
        print(map)
