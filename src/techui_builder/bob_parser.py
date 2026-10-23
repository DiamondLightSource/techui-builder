import logging
import re
from dataclasses import dataclass
from pathlib import Path

from lxml.objectify import ObjectifiedElement

from techui_builder.models import BobFile, BobWidget, MacroMap
from techui_builder.utils import _INDEX_BOB_NAME_RE, WidgetType, read_bob

logger_ = logging.getLogger(__name__)


@dataclass
class BobParser:
    """
    The BobParser class is responsible for parsing .bob files and extracting relevant
    information such as widgets and macros. It provides methods to read the .bob file,
    parse its contents, and return a structured representation of the data.
    """

    bob_path: Path

    def _parse_widgets(self, container: ObjectifiedElement) -> list[BobWidget]:
        """
        Parses the widgets from the given container element
        and returns a list of BobWidget instances.
        """
        result = []

        for element in container.iterchildren("widget"):
            if element.get("type", default="") not in WidgetType:
                continue
            # Find the name and prefix of the widget
            name_element = element.find("name")
            name = name_element.text if name_element is not None else ""
            prefix_element = element.find("pv_name")
            prefix = prefix_element.text if prefix_element is not None else ""

            macros: MacroMap = {}
            macro_pairs = re.fullmatch(_INDEX_BOB_NAME_RE, name if name else "")

            if macro_pairs is None:
                print(f"No match for {name!r}")
            else:
                print(f"Match: {macro_pairs.group(0)!r}")
                for number, value in enumerate(macro_pairs.groups(), start=1):
                    print(f"Group {number}: {value!r}")

                list_types = ("extras", "status")
                for key, value in macro_pairs.groupdict().items():
                    if key not in list_types:
                        macros[key] = value
                    else:
                        value = value[1:-1]
                        macros[key] = [v.strip() for v in value.split(",") if v.strip()]

            # Create a BobWidget instance for the widget
            widget = BobWidget(
                name=name or "",
                widget_type=element.get("type", default=""),
                macros=macros,
                element=element,
                children=None,
                prefix=prefix or "",
            )

            if widget.widget_type in WidgetType:
                result.append(widget)

        return result

    def parse_bob(
        self,
    ) -> BobFile:
        """
        Parses the .bob file specified by the bob_path
        attribute and returns a BobFile instance
        """
        tree, _, display_macros = read_bob(self.bob_path)
        root = tree.getroot()

        return BobFile(
            path=self.bob_path,
            macros=display_macros,
            tree=tree,
            widgets=self._parse_widgets(root),
        )
