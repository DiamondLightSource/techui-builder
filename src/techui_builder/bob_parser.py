import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml.etree import ElementTree
from lxml.objectify import ObjectifiedElement

from techui_builder.utils import (
    read_bob,
)

logger_ = logging.getLogger(__name__)

macros = dict[str, str]
WidgetDict = dict[str, ObjectifiedElement]
TreeWidgetDictTuple = tuple[ElementTree, WidgetDict]
MacroTreeTuple = tuple[macros, TreeWidgetDictTuple]
IndexObjectDict = dict[Path, MacroTreeTuple]


@dataclass
class BobParser:
    bob_path: Path
    index_trees: IndexObjectDict = field(default_factory=dict, init=False, repr=False)

    def read_bob(self):
        # Read the bob file
        tree, widget_dict, macros = read_bob(self.bob_path)
        self.index_trees[self.bob_path] = (macros, (tree, widget_dict))
        print(self.index_trees)
        return self.index_trees
