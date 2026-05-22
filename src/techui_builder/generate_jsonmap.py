import json
import logging
from collections import defaultdict
from dataclasses import _MISSING_TYPE, dataclass, field
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from lxml import etree, objectify
from lxml.objectify import ObjectifiedElement

from techui_builder._logger import Logger
from techui_builder.models import TechUi

logger_ = logging.getLogger(__name__)


def log_level(level: str):
    Logger(level)


app = typer.Typer(
    pretty_exceptions_show_locals=False,
    help="""
    A script for generating a .json file mapping of phoebus gui screens.

    This is the required file structure:\n
\n
    ixx-services\n
    `-- synoptic\n
    .   |-- techui-support/\n
    |   |   `-- ...\n
    .   |-- techui.yaml\n
    .   `-- index.bob\n
""",
)


@dataclass
class JsonMap:
    file: str
    display_name: str | None
    exists: bool = True
    duplicate: bool = False
    children: list["JsonMap"] = field(default_factory=list)
    macros: dict[str, str] = field(default_factory=dict)
    error: str = ""


@dataclass
class JsonMapGenerator:
    bob_path: Path = field(default=Path("index.bob"))
    techui: Path = field(default=Path("techui.yaml"))

    def __post_init__(self):
        # Get the directory to that holds the bob file and techui_yaml,
        self._write_directory: Path = self.bob_path.parent
        if self.techui == Path("techui.yaml"):
            self.techui = self._write_directory.joinpath("techui.yaml")
        try:
            self.techui_yaml: TechUi = TechUi.model_validate(
                yaml.safe_load(self.techui.read_text(encoding="utf-8"))
            )
        except Exception as e:
            logger_.error(f"Error loading techui.yaml: {e}")
            raise

    def generate_json_map(
        self,
        screen_path: Path,
        dest_path: Path,
        current_component_name: str | None = None,
        name_elem: str | None = None,
    ) -> JsonMap:
        """Recursively generate JSON map from .bob file tree"""

        # ------------ USEFUL FUNCTIONS ------------

        def _get_display_name(
            name_element: str | None, component_name: str | None, file_path: Path
        ):
            # Validated screen names don't get renegerated
            name = name_element
            display_name = self._get_component_label(
                name_element,
                component_name,
                name,
            )
            # Create valid displayName
            display_name = self._parse_display_name(display_name, file_path)
            return display_name

        def _next_file_crawl(
            file_path: Path,
            destination_path: Path,
            name_element: str | None,
            component_name: str | None,
            display_name: str | None,
            macro_dictionary: dict[str, Any],
        ):
            # TODO: misleading var name?
            next_file_path = destination_path.joinpath(file_path)

            # Crawl the next file
            if next_file_path.is_file():
                # TODO: investigate non-recursive approaches?
                child_node = self.generate_json_map(
                    next_file_path,
                    destination_path,
                    current_component_name=component_name,
                    name_elem=name_element,
                )
            else:
                child_node = JsonMap(
                    str(file_path),
                    display_name,
                    exists=("IOC" in macro_dictionary or ("https:/" in str(file_path))),
                )

            return child_node

        # ------------------------------------------

        # Create initial node at top of .bob file
        current_node = JsonMap(
            str(screen_path.resolve().relative_to(self._write_directory.resolve())),
            display_name=None,
        )

        # Get Current Component
        if (
            current_component_name is None
            and screen_path.stem in self.techui_yaml.components
        ):
            current_component_name = screen_path.stem

        abs_path = screen_path.absolute()

        try:
            # Create xml tree from .bob file
            tree = objectify.parse(abs_path)
            root: ObjectifiedElement = tree.getroot()

            # Set top level display name from root element
            current_node.display_name = self._parse_display_name(
                root.name.text, screen_path
            )
            current_node.display_name = self._get_component_label(
                name_elem,
                current_component_name,
                current_node.display_name,
            )
            # Find all <widget> elements
            widgets = [
                w
                for w in root.findall(".//widget")
                if w.get("type", default=None)
                in ["symbol", "action_button", "embedded", "navtabs"]
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

                        # Use file, name, and macro elements
                        file_elem = open_display.file
                        name_elem = widget_elem.name.text
                        macro_dict = self._get_macros(open_display)

                    case "embedded":
                        file_elem = widget_elem.file
                        name_elem = widget_elem.name.text
                        macro_dict = self._get_macros(widget_elem)

                    case "navtabs":
                        tabs = _get_nav_tabs(widget_elem)
                        if tabs is None:
                            continue

                        for tab in tabs:
                            name_elem = tab.name.text
                            file_elem = tab.file
                            macro_dict = self._get_macros(tab)

                            # Extract file path from file_elem
                            # Keep raw string to preserve urls
                            file_text = file_elem.text.strip() if file_elem.text else ""
                            file_path = Path(file_text)

                            # If file is already a .bob file, skip it
                            if not file_path.suffix == ".bob":
                                continue

                            display_name = _get_display_name(
                                name_elem, current_component_name, file_path
                            )

                            child_node = _next_file_crawl(
                                file_path,
                                dest_path,
                                name_elem,
                                current_component_name,
                                display_name,
                                macro_dict,
                            )

                            child_node.macros = macro_dict
                            # TODO: make this work for only list[JsonMap]
                            assert isinstance(current_node.children, list)
                            # TODO: fix typing
                            current_node.children.append(child_node)

                        # We have already done the logic, so skip to the next widget
                        continue

                    case _:
                        continue

                # Extract file path from file_elem
                # Keep raw string to preserve urls
                file_text = file_elem.text.strip() if file_elem.text else ""
                file_path = Path(file_text)

                # If file is already a .bob file, skip it
                if not file_path.suffix == ".bob":
                    continue

                # Create valid displayName
                display_name = _get_display_name(
                    name_elem, current_component_name, file_path
                )

                child_node = _next_file_crawl(
                    file_path,
                    dest_path,
                    name_elem,
                    current_component_name,
                    display_name,
                    macro_dict,
                )

                if widget_type == "embedded":
                    for embedded_child in child_node.children:
                        embedded_child.macros = {**embedded_child.macros, **macro_dict}
                        embedded_child.display_name = display_name
                        embedded_child.exists = "IOC" in macro_dict or (
                            "https://" in str(embedded_child.file)
                        )
                        current_node.children.append(embedded_child)

                else:
                    child_node.macros = macro_dict
                    # TODO: make this work for only list[JsonMap]
                    assert isinstance(current_node.children, list)
                    # TODO: fix typing
                    current_node.children.append(child_node)

        except etree.ParseError as e:
            current_node.error = f"XML parse error: {e}"
        except Exception as e:
            current_node.error = str(e)

        self._fix_names_json_map(current_node)

        return current_node

    def _get_component_label(
        self,
        name_elem: str | None,
        current_component_name: str | None,
        display_name: str | None,
    ) -> str | None:
        """
        Get display name from the label or child labels if they exist, otherwise return
        name_elem or existing display_name if name_elem is None.
        """
        component = self.techui_yaml.components
        if name_elem is not None:
            if name_elem in component.keys() and component[name_elem].label is not None:
                display_name = component[name_elem].label
            elif (
                current_component_name is not None
                and (current_component_name in component.keys())
                and (component[current_component_name].child_labels is not None)
            ):
                child_labels = component[current_component_name].child_labels
                if child_labels is not None:
                    # Because name_elem is initially grabbed from
                    #  the .bob file, the generated .bobfile might have
                    # already propagated the child label from techui.yaml
                    if name_elem in child_labels.values():
                        display_name = name_elem
                    # In the case of screens not regenerated, such as validated screens,
                    # the name text will not be updated to the childlabel,so we check
                    # keys solely for generating the json_map from the top level .bob.
                    elif name_elem in child_labels:
                        display_name = child_labels[name_elem]
        return display_name

    def _get_macros(self, element: ObjectifiedElement):
        if hasattr(element, "macros"):
            macros = element.macros.getchildren()
            if macros is not None:
                return {
                    str(macro.tag): macro.text
                    for macro in macros
                    if macro.text is not None
                }
        return {}

    def _parse_display_name(self, name: str | None, file_path: Path) -> str | None:
        """Parse display name from <name> tag or file_path"""

        if name:
            # Return name tag text as displayName
            return name

        elif file_path.name:
            # Use tail without file ext as displayName
            return file_path.name[: -sum(len(suffix) for suffix in file_path.suffixes)]

        else:
            # Populate displayName with null
            return None

    def _fix_names_json_map(
        self,
        node: JsonMap,
    ) -> None:
        """Recursively fix duplicate display names in children"""
        if not node.children:
            return

        # group by display_name
        name_groups: defaultdict[str | None, list] = defaultdict(list)
        for child in node.children:
            name_groups[child.display_name].append(child)

        # fix duplicates by appending identifiers
        for name, children in name_groups.items():
            if name and len(children) > 1:
                # append pv names when present

                for child in children:
                    if "P" in child.macros:
                        child.display_name = f"{name} ({child.macros['P']})"

                # append NO PV NAME and enumeration when there is no pv name
                no_pv_children = [c for c in children if "P" not in c.macros]
                for i, child in enumerate(no_pv_children, 1):
                    child.display_name = f"{name} (NO PV NAME {i})"

        # recursively fix children
        for child in node.children:
            self._fix_names_json_map(child)

    def write_json_map(
        self,
    ):
        """
        Maps the valid entries from the ioc.yaml file
        to the required screen in *-mapping.yaml
        """
        if not self.bob_path.exists():
            raise FileNotFoundError(
                f"Cannot generate json map for {self.bob_path}. Has it been generated?"
            )

        map = self.generate_json_map(self.bob_path, self._write_directory)
        with open(self._write_directory.joinpath("JsonMap.json"), "w") as f:
            f.write(
                json.dumps(map, indent=4, default=lambda o: _serialise_json_map(o))
                + "\n"
            )


# Function to convert the JsonMap objects into dictionaries,
# while ignoring default values
def _serialise_json_map(map: JsonMap) -> dict[str, Any]:
    def _check_default(key: str, value: Any):
        # Is a default factory used? (e.g. list, dict, ...)
        if not isinstance(
            JsonMap.__dataclass_fields__[key].default_factory, _MISSING_TYPE
        ):
            # If so, check if value is the same as default factory
            default = JsonMap.__dataclass_fields__[key].default_factory()
        else:
            # If not, check if value is the default value
            default = JsonMap.__dataclass_fields__[key].default
        return value == default

    d = {}

    # Loop over everything in the json map object's dictionary
    for key, val in map.__dict__.items():
        # If children has nested JsonMap object, serialise that too
        if key == "children" and len(val) > 0:
            val = [_serialise_json_map(v) for v in val]

        # only include any items if they are not the default value
        if _check_default(key, val):
            continue

        d[key] = val

    # Rename display_name to displayName for JSON camel case convention
    if "display_name" in d:
        d["displayName"] = d.pop("display_name")

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
        # TODO: Do widgets always have a name attr, or _can_ it be empty??
        name = element.name

        parent_name = p.name if (p := element.getparent()) is not None else None

        logger_.error(
            f"Actions group not found in component [bold]{name}[/bold] on "
            f"[bold]{parent_name}[/bold]"
        )


def _get_nav_tabs(element: ObjectifiedElement) -> list[ObjectifiedElement] | None:
    try:
        element_tabs = element.tabs
        assert element_tabs is not None

        tabs = list(element_tabs.iterchildren("tab"))

        return tabs

    except AttributeError:
        # TODO: Find better way of handling there being no "tabs" group
        # TODO: Do widgets always have a name attr, or _can_ it be empty??
        name = element.name

        parent_name = p.name if (p := element.getparent()) is not None else None

        logger_.error(
            f"Tabs group not found in component [bold]{name}[/bold] on "
            f"[bold]{parent_name}[/bold]"
        )


@app.callback(invoke_without_command=True)
def generate_jsonmap(
    bob_path: Annotated[
        Path,
        typer.Argument(help="Top level bobfile to generate json mapping from."),
    ],
    loglevel: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-l",
            help="Set log level to INFO, DEBUG, WARNING, ERROR or CRITICAL",
            case_sensitive=False,
            callback=log_level,
        ),
    ] = "INFO",
) -> None:
    """Default function called from cmd line tool."""
    jg = JsonMapGenerator(bob_path=bob_path)
    jg.write_json_map()
    logger_.info(
        f"Json map generated for {jg.techui_yaml.beamline.location} (from index.bob)"
    )


if __name__ == "__main__":
    app()
