import yaml

from phoebus_guibuilder.datatypes import Beamline, Component, Entry
from phoebus_guibuilder.git_utilities import GitYaml


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

    def find_services_extract_ioc(
        self,
    ):
        """
        Finds the related folders in the services repo
        and extracts the related entites with the matching prefixes
        """

        for component in self.components:
            print(component.P)
            ioc_yaml = GitYaml(self.beamline.dom, prefix=component.P).fetch_ioc_yaml()
            if ioc_yaml is not None:
                self.extract_valid_entities(
                    ioc_yaml,
                    component=component,
                )
            else:
                print("Cannot find the yaml file, check the repo")

    def extract_valid_entities(self, ioc_yaml: str, component: Component):
        """
        Extracts the entities in ioc.yaml matching the defined prefix
        """

        entities: list[dict[str, str]] = []
        component_match = f"{component.P}:{component.R}"

        with open(ioc_yaml) as ioc:
            conf = yaml.safe_load(ioc)
            entities = conf["entities"]
            print(entities)
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
            print(self.valid_entities)

    def gui_map(self, entrys: list[Entry]):
        """
        Maps the valid entities from the ioc.yaml file
        to the required screen in gui_map.yaml
        """

        gui_map = "/BLGui/BLGuiApp/opi/bob/gui_map.yaml"

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
