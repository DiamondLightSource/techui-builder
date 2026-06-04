import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Template

from techui_builder.generate import Generator
from techui_builder.models import Entity, SupportEntity, TechUi, TechUiSupport
from techui_builder.validator import Validator

logger_ = logging.getLogger(__name__)


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
    _write_directory: Path = field(init=False, repr=False)

    def __post_init__(self):
        # Populate beamline and components
        self.conf = TechUi.model_validate(
            yaml.safe_load(self.techui.read_text(encoding="utf-8"))
        )

    def setup(self):
        """
        Run intial setup, e.g. extracting entries
        from service ioc.yaml or fastcs.yaml.
        """
        # This needs to be before _read_map()
        self.support_path = self._write_directory.joinpath("techui-support")

        self._read_map()

        self._extract_services()

        self.clean_files()

        self.generator = Generator(
            self._write_directory,
            self.conf.beamline.url,
            self.support_path,
            self.techui_support,
        )

    def _read_map(self):
        """Read the techui-support.yaml file from techui-support."""
        support_yaml = self.support_path.joinpath("techui-support.yaml").absolute()
        logger_.debug(f"techui-support.yaml location: {support_yaml}")

        self.techui_support = TechUiSupport.model_validate(
            yaml.safe_load(support_yaml.read_text(encoding="utf-8"))
        )

    def clean_files(self):
        exclude = {"index.bob"}
        bobs = [
            bob
            for bob in self._write_directory.glob("*.bob")
            if bob.name not in exclude
        ]

        self.validator = Validator(bobs)
        self.validator.check_bobs()

        # Get bobs that are only present in the bobs list (i.e. generated)
        self.generated_bobs = list(set(bobs) ^ set(self.validator.validate.values()))

        logger_.info("Preserving edited screens for validation.")
        logger_.debug(f"Screens to validate: {list(self.validator.validate.keys())}")

        logger_.info("Cleaning synoptic directory of generated screens.")

        try:
            # Find the JsonMap file
            json_map_file = next(self._write_directory.glob("JsonMap.json"))
            # If it exists, we want to remove it too
            generated_files = [*self.generated_bobs, json_map_file]
        except StopIteration:
            generated_files = self.generated_bobs

        # Remove any generated files that exist
        for file_ in generated_files:
            logger_.debug(f"Removing generated file: {file_.name}")
            os.remove(file_)

    def _extract_services(self):
        """
        Finds the services folders in the services directory
        and extracts all entites
        """

        # Loop over every dir in services, ignoring anything that isn't a service
        for service in self._services_dir.glob(f"{self.conf.beamline.domain}-*-*-*"):
            service_name = service.name
            # If service doesn't exist, file open will fail throwing exception
            try:
                service_yaml_dir = service.joinpath("config")
                service_yaml = next(service_yaml_dir.glob("*.yaml"), None)
                if service_yaml is None:
                    raise OSError()

                self._extract_entities(
                    service_name=service_name,
                    service_yaml=service_yaml,
                )

            except OSError:
                logger_.error(
                    "No ioc.yaml or fastcs.yaml found for service: "
                    f"[bold]{service_name}[/bold]. Does it exist?"
                )

    def _extract_entities(self, service_name: str, service_yaml: Path):
        """
        Extracts the entries in ioc.yaml matching the defined prefix
        """

        with open(service_yaml) as ioc:
            ioc_conf: dict[str, list[dict[str, str]]] = yaml.safe_load(ioc)

            for key in ioc_conf.keys():
                _regex = re.compile(r"^(?:(entities)|(controllers))$")
                match = _regex.match(key)
                if match:
                    entity_key = match.group()

                    for entity in ioc_conf[entity_key]:
                        if entity["type"] in self.techui_support.support_modules:
                            support_mapping: SupportEntity = (
                                self.techui_support.support_modules[entity["type"]]
                            )
                            support_macros = support_mapping.macros

                            macros = {
                                k: v for k, v in entity.items() if k in support_macros
                            }

                            prefix_template = Template(support_mapping.prefix)
                            prefix: str = prefix_template.render(macros)

                            # Create Entity and append to entity list
                            new_entity = Entity(
                                service_name=service_name,
                                type=entity["type"],
                                desc=entity.get("desc", None),
                                prefix=prefix,
                                macros=macros,
                            )

                            pv_root = prefix.split(":", maxsplit=1)[0]
                            self.entities[pv_root].append(new_entity)
                    break

    def _generate_screen(self, screen_name: str):
        self.generator.build_screen(screen_name)
        self.generator.write_screen(screen_name, self._write_directory)

    def _validate_screen(self, screen_name: str):
        # Get the generated widgets to validate against
        widgets = self.generator.widgets
        widget_group = self.generator.group
        assert widget_group is not None
        widget_group_name = widget_group.get_element_value("name")
        self.validator.validate_bob(screen_name, widget_group_name, widgets)

    def create_screens(self):
        """Create the screens for each component in techui.yaml"""
        if len(self.entities) == 0:
            logger_.critical(
                "No ioc entities found. This [italic]normally[/italic]"
                " suggests an issue with finding ixx-services."
            )
            exit()

        # Loop over every component defined in techui.yaml and locate
        # any extras defined
        for component_name, component in self.conf.components.items():
            screen_entities: list[Entity] = []

            # ONLY IF there is a matching component and entity, generate a screen
            if component.prefix in self.entities.keys():
                # Populate child labels for any entities
                # with the same prefix as the component
                for entity in self.entities[component.prefix]:
                    entity.child_labels = component.child_labels

                screen_entities.extend(self.entities[component.prefix])

                if component.extras is not None:
                    # If component has any extras, add them to the entries to generate
                    for extra_p in component.extras:
                        if extra_p not in self.entities.keys():
                            logger_.error(
                                f"Extra prefix {extra_p} for {component_name} does not"
                                " exist."
                            )
                            continue
                        screen_entities.extend(self.entities[extra_p])

                # This is used by both generate and validate,
                # so called beforehand for tidyness
                self.generator.build_widgets(component_name, screen_entities)
                self.generator.build_groups(component_name, self.conf.components)

                screens_to_validate = list(self.validator.validate.keys())

                if component_name in screens_to_validate:
                    self._validate_screen(component_name)
                else:
                    self._generate_screen(component_name)

            else:
                logger_.warning(
                    f"{self.techui.name}: The prefix [bold]{component.prefix}[/bold] "
                    f"set in the component [bold]{component_name}[/bold] does not match"
                    " any P field in the ioc.yaml files in services"
                )
