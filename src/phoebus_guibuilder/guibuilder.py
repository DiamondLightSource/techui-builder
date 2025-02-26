import os
import re

import yaml

from phoebus_guibuilder.datatypes import Beamline, Component, Entry


class Guibuilder:
    """
    This class provides the functionality to process the required
    create_gui.yaml file into screens mapped from ioc.yaml and
    gui_map.yaml files.

    """

    def __init__(self, create_gui_yaml: str):
        self.components: list[Component] = []

        self.beamline: Beamline

        self.valid_entities: list[Entry] = []

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
        self.git_pull_submodules()

        services_directory = (
            self.beamline.dom + "-services/services"
        )  # TODO: rm hardcoding, map to services.
        path = f"{services_directory}"
        files = os.listdir(path)

        # Attempting to match the prefix to the files in the services directory
        pattern = "^(.*)-(.*)-(.*)"

        for component in self.components:
            domain: re.Match[str] | None = re.match(pattern, component.P)
            assert domain is not None, "Empty Prefix Field"

            for file in files:
                match = re.match(pattern, file)
                if match:
                    if match.group(1) == domain.group(1).lower():
                        if os.path.exists(f"{path}/{file}/config/ioc.yaml"):
                            self.extract_valid_entities(
                                ioc_yaml=f"{path}/{file}/config/ioc.yaml",
                                component=component,
                            )
                        else:
                            print(f"No ioc.yaml file for service: {file}")
        os.system(f"rm -rf ./{self.beamline.dom}-services/ ./techui-support/")

    def extract_valid_entities(self, ioc_yaml: str, component: Component):
        """
        Extracts the entities in ioc.yaml matching the defined prefix
        """

        entities: list[dict[str, str]] = []
        component_match = f"{component.P}:{component.R}"

        with open(ioc_yaml) as ioc:
            conf = yaml.safe_load(ioc)
            entities = conf["entities"]
            for entity in entities:
                if (
                    "P" in entity.keys() and entity["P"] == component_match
                ):  # the suffix could be M, could be R
                    self.valid_entities.append(
                        Entry(
                            type=entity["type"],
                            DESC=None,
                            P=entity["P"],
                            M=None,
                            R=None,
                        )
                    )
                    if "M" in entity.keys():
                        self.valid_entities[-1].M = entity["M"]

    def gui_map(self, entrys: list[Entry]):
        """
        Maps the valid entities from the ioc.yaml file
        to the required screen in gui_map.yaml
        """

        gui_map = "./GuiMap/gui_map.yaml"

        with open(gui_map) as map:
            conf = yaml.safe_load(map)

            for entry in entrys:
                print(entry.type)
                if conf[entry.type]:
                    print(
                        conf[entry.type]["file"]
                    )  # Find correct .bob file, and injet macros
                    # TODO:  create a copy of the file, and replace the required macros
                    # TODO:  return the file to guibuilder

                else:
                    print("No BOB available")

    def git_pull_submodules(self):
        """
        Method which helps pull the required modules in as
        submodules and removes all traces of submodules.
        """
        services_repo = f"git submodule add --force\
                        https://github.com/epics-containers/{self.beamline.dom}-services.git"
        gui_map_repo = "git submodule add --force https://github.com/adedamola-sode/techui-support.git"

        submodules = "echo ''> .gitmodules & git submodule sync"
        rm_repos = f"rm -rf ./{self.beamline.dom}-services/ ./techui-support/"
        unstage = f"git restore --staged .gitmodules\
              {self.beamline.dom}-services techui-support"

        os.system(submodules)
        os.system(rm_repos)
        os.system(services_repo)
        os.system(gui_map_repo)
        os.system(unstage)
        os.system(submodules)
