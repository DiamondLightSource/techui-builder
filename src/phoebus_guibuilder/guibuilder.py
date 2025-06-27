import json
from collections.abc import MutableMapping
from pathlib import Path

import lxml.etree as etree
import yaml

from phoebus_guibuilder.datatypes import Beamline, Component, Entry
from phoebus_guibuilder.screen import TechUIScreens as Screen

# Recursive type for Json map file
type json_map = MutableMapping[str, str | list["json_map"]]


class Guibuilder:
    """
    This class provides the functionality to process the required
    create_gui.yaml file into screens mapped from ioc.yaml and
    gui_map.yaml files.

    """

    def __init__(self, create_gui_yaml: str):
        self.components: list[Component] = []

        self.beamline: Beamline

        self.entities: list[Entry] = []

        self.create_gui: str = create_gui_yaml

        self.extract_from_create_gui()

    def extract_from_create_gui(
        self,
    ):
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

    def find_services_folders(
        self,
    ):
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
                self.extract_entities(
                    ioc_yaml=f"{path}/{service_name}/config/ioc.yaml",
                    component=component,
                )
            except OSError:
                print(f"No ioc.yaml file for service: {service_name}. Does it exist?")

    def extract_entities(self, ioc_yaml: str, component: Component):
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
                        DESC=component.name,
                        P=entity["P"],
                        M=entity["M"].removeprefix(":") or None,
                        R=entity["R"].removeprefix(":") or None,
                    )
                    self.entities.append(entry)

    def generate_json_map(
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
                    next_node = self.generate_json_map(next_file_path, visited)
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
    def gui_map(self, file_name: Path = Path("motor.bob")):
        """
        Maps the valid entities from the ioc.yaml file
        to the required screen in gui_map.yaml
        """

        gui_map = "./techui-support/gui_map.yaml"

        with open(gui_map) as map:
            conf = yaml.safe_load(map)
            Screen(self.entities, conf)
            self.generate_json_map(file_name)
