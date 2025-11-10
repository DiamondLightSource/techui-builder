import json
import logging
from collections import defaultdict
from dataclasses import _MISSING_TYPE, dataclass, field
from pathlib import Path
from typing import Any

import yaml
from lxml import etree, objectify
from lxml.objectify import ObjectifiedElement

from techui_builder.generate import Generator
from techui_builder.models import Entity, TechUi

LOGGER = logging.getLogger(__name__)


@dataclass
class json_map:
    file: str
    exists: bool = True
    duplicate: bool = False
    children: list["json_map"] = field(default_factory=list)
    macros: dict[str, str] = field(default_factory=dict)
    error: str = ""


@dataclass
class Builder:
    """
    This class provides the functionality to process the required
    techui.yaml file into screens mapped from ioc.yaml and
    *-mapping.yaml files.

    By default it looks for a `techui.yaml` file in the same dir
    of the script Guibuilder is called in. Optionally a custom path
    can be declared.

    """

    techui: Path = field(default=Path("techui.yaml"))

    entities: defaultdict[str, list[Entity]] = field(
        default_factory=lambda: defaultdict(list), init=False
    )
    _services_dir: Path = field(init=False, repr=False)
    _gui_map: dict = field(init=False, repr=False)
    _write_directory: Path = field(default=Path("opis"), init=False, repr=False)

    def __post_init__(self):
        # Populate beamline and components
        self.conf = TechUi.model_validate(
            yaml.safe_load(self.techui.read_text(encoding="utf-8"))
        )

    def setup(self):
        """Run intial setup, e.g. extracting entries from service ioc.yaml."""
        self._extract_services()
        synoptic_dir = self._write_directory
        self.generator = Generator(synoptic_dir)

    def _extract_services(self):
        """
        Finds the services folders in the services directory
        and extracts all entites
        """

        # Loop over every dir in services, ignoring anything that isn't a service
        for service in self._services_dir.glob(f"{self.conf.beamline.long_dom}-*-*-*"):
            # If service doesn't exist, file open will fail throwing exception
            try:
                self._extract_entities(ioc_yaml=service.joinpath("config/ioc.yaml"))
            except OSError:
                LOGGER.error(
                    f"No ioc.yaml file for service: [bold]{service.name}[/bold]. \
Does it exist?"
                )

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

    def _generate_screen(self, screen_name: str, screen_components: list[Entity]):
        self.generator.load_screen(screen_name, screen_components)
        self.generator.build_groups()
        self.generator.write_screen(self._write_directory)

    def generate_screens(self):
        """Generate the screens for each component in techui.yaml"""
        if len(self.entities) == 0:
            LOGGER.critical("No ioc entities found, has setup() been run?")
            exit()

        # Loop over every component defined in techui.yaml and locate
        # any extras defined
        for component_name, component in self.conf.components.items():
            screen_entities: list[Entity] = []
            # ONLY IF there is a matching component and entity, generate a screen
            if component.prefix in self.entities.keys():
                screen_entities.extend(self.entities[component.prefix])
                if component.extras is not None:
                    # If component has any extras, add them to the entries to generate
                    for extra_p in component.extras:
                        if extra_p not in self.entities.keys():
                            LOGGER.error(
                                f"Extra prefix {extra_p} for {component_name} does not \
exist."
                            )
                            continue
                        screen_entities.extend(self.entities[extra_p])

                self._generate_screen(component_name, screen_entities)
            else:
                LOGGER.warning(
                    f"{self.techui.name}: The prefix [bold]{component.prefix}[/bold]\
 set in the component [bold]{component_name}[/bold] does not match any P field in the\
 ioc.yaml files in services"
                )

    def _generate_json_map(
        self, screen_path: Path, dest_path: Path, visited: set[Path] | None = None
    ) -> json_map:
        def _get_macros(element: ObjectifiedElement):
            if hasattr(element, "macros"):
                macros = element.macros.getchildren()
                if macros is not None:
                    return {
                        str(macro.tag): macro.text
                        for macro in macros
                        if macro.text is not None
                    }
            return {}

        if visited is None:
            visited = set()

        current_node = json_map(str(screen_path))

        abs_path = screen_path
        dest_path = dest_path
        if abs_path in visited:
            current_node.exists = True
            current_node.duplicate = True
            return current_node
        visited.add(abs_path)

        try:
            tree = objectify.parse(abs_path)
            root: ObjectifiedElement = tree.getroot()

            # Find all <widget> elements
            widgets = [
                w
                for w in root.findall(".//widget")
                if w.get("type", default=None)
                # in ["symbol", "embedded", "action_button"]
                in ["symbol", "action_button"]
            ]

            for widget_elem in widgets:
                # Obtain macros associated with file_elem
                macro_dict: dict[str, str] = {}
                widget_type = widget_elem.get("type", default=None)

                match widget_type:
                    case "symbol" | "action_button":
                        open_display = _get_action_group(widget_elem)
                        if open_display is None:
                            continue
                        file_elem = open_display.file

                        macro_dict = _get_macros(open_display)
                    # case "embedded":
                    #     file_elem = widget_elem.file
                    #     macro_dict = _get_macros(widget_elem)
                    case _:
                        continue

                # Extract file path from file_elem
                file_path = Path(file_elem.text.strip() if file_elem.text else "")
                # If file is already a .bob file, skip it
                if not file_path.suffix == ".bob":
                    continue

                # TODO: misleading var name?
                next_file_path = dest_path.joinpath(file_path)

                # Crawl the next file
                if next_file_path.is_file():
                    # TODO: investigate non-recursive approaches?
                    child_node = self._generate_json_map(
                        next_file_path, dest_path, visited
                    )
                else:
                    child_node = json_map(str(file_path), exists=False)

                child_node.macros = macro_dict
                # TODO: make this work for only list[json_map]
                assert isinstance(current_node.children, list)
                # TODO: fix typing
                current_node.children.append(child_node)

        except etree.ParseError as e:
            current_node.error = f"XML parse error: {e}"
        except Exception as e:
            current_node.error = str(e)

        return current_node

    def write_json_map(
        self,
        synoptic: Path = Path("example/t01-services/synoptic/index.bob"),
        dest: Path = Path("example/t01-services/synoptic"),
    ):
        """
        Maps the valid entries from the ioc.yaml file
        to the required screen in *-mapping.yaml
        """
        if not synoptic.exists():
            raise FileNotFoundError(
                f"Cannot generate json map for {synoptic}. Has it been generated?"
            )

        map = self._generate_json_map(synoptic, dest)
        with open(dest.joinpath("json_map.json"), "w") as f:
            f.write(json.dumps(map, indent=4, default=lambda o: _serialise_json_map(o)))


# Function to convert the json_map objects into dictionaries,
# while ignoring default values
def _serialise_json_map(map: json_map) -> dict[str, Any]:
    def _check_default(key: str, value: Any):
        # Is a default factory used? (e.g. list, dict, ...)
        if not isinstance(
            json_map.__dataclass_fields__[key].default_factory, _MISSING_TYPE
        ):
            # If so, check if value is the same as default factory
            default = json_map.__dataclass_fields__[key].default_factory()
        else:
            # If not, check if value is the default value
            default = json_map.__dataclass_fields__[key].default
        return value == default

    d = {}

    # Loop over everything in the json map object's dictionary
    for key, val in map.__dict__.items():
        # If children has nested json_map object, serialise that too
        if key == "children" and len(val) > 0:
            val = [_serialise_json_map(v) for v in val]

        # only include any items if they are not the default value
        if _check_default(key, val):
            continue

        d[key] = val

    return d


# File and desc are under the "actions",
# so the corresponding tag needs to be found
def _get_action_group(element: ObjectifiedElement) -> ObjectifiedElement | None:
    try:
        actions = element.actions
        assert actions is not None
        for action in actions.iterchildren("action"):
            if action.get("type", default=None) == "open_display":
                return action
        return None
    except AttributeError:
        # TODO: Find better way of handling there being no "actions" group
        LOGGER.error(f"Actions group not found in component: {element.text}")
