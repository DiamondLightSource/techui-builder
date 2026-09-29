import logging
from dataclasses import dataclass
from pathlib import Path

from lxml.objectify import ObjectifiedElement

from techui_builder.models import BobFile, BobWidget
from techui_builder.utils import WidgetType, _get_macros, read_bob

logger_ = logging.getLogger(__name__)


@dataclass
class BobParser:
    bob_path: Path

    def _parse_widgets(self, container: ObjectifiedElement) -> list[BobWidget]:
        result = []

        for element in container.iterchildren("widget"):
            name_element = element.find("name")
            name = name_element.text if name_element is not None else ""

            widget = BobWidget(
                name=name or "",
                widget_type=element.get("type", default=""),
                macros=_get_macros(element),
                element=element,
                children=None,
            )
            if widget.widget_type == "group":
                widget.children = self._parse_widgets(element)

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
