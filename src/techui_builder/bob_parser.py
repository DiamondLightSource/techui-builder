import logging
from dataclasses import dataclass
from pathlib import Path

from lxml.objectify import ObjectifiedElement

from techui_builder.models import BobFile, BobWidget, MacroMap
from techui_builder.utils import WidgetType, _get_action_group, _get_macros, read_bob

logger_ = logging.getLogger(__name__)


@dataclass
class BobParser:
    bob_path: Path

    def _parse_widgets(self, container: ObjectifiedElement) -> list[BobWidget]:
        result = []

        for element in container.iterchildren("widget"):
            # Find the name and prefix of the widget
            name_element = element.find("name")
            name = name_element.text if name_element is not None else ""
            prefix_element = element.find("pv_name")
            prefix = prefix_element.text if prefix_element is not None else ""

            # Collect the macros from the widget through its action group if it has one
            action_group = _get_action_group(element)
            raw_macros = _get_macros(
                action_group if action_group is not None else element
            )

            # Create a MacroMap from the raw macros
            macros: MacroMap = {}

            for key, value in raw_macros.items():
                macros[key] = value

            for key in ("extras", "status"):
                value = raw_macros.get(key)
                if value is not None:
                    macros[key] = value.split(", ")

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
        tree, _, display_macros = read_bob(self.bob_path)
        root = tree.getroot()

        return BobFile(
            path=self.bob_path,
            macros=display_macros,
            tree=tree,
            widgets=self._parse_widgets(root),
        )
