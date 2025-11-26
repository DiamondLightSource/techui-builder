import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from phoebusgen.widget.widgets import ActionButton, EmbeddedDisplay

from techui_builder.utils import read_bob

LOGGER = logging.getLogger(__name__)


@dataclass
class Validator:
    bobs: list[Path]
    validate: dict[str, Path] = field(
        default_factory=defaultdict, init=False, repr=False
    )

    def check_bobs(self):
        for bob in self.bobs:
            self._check_bob(bob)

    def _check_bob(self, bob_path: Path):
        # etree has to used as objectify ignore comments
        xml = etree.parse(bob_path)
        # fetch all the comments at the base of the tree
        comments = list(xml.getroot().itersiblings(tag=etree.Comment, preceding=True))
        if len(comments) > 0:
            # Check if any comments found are the manually saved tag
            if any(str(comment).startswith("<!--Saved on ") for comment in comments):
                self.validate[bob_path.name.removesuffix(".bob")] = bob_path

    def _read_bob(self, path: Path):
        tree, widgets = read_bob(path)
        return tree.getroot(), widgets

    def validate_bob(
        self,
        screen_name: str,
        widget_group_name: str,
        pwidgets: list[EmbeddedDisplay | ActionButton],
    ):
        path = self.validate[screen_name]
        _, file_groups = self._read_bob(path)

        if widget_group_name not in file_groups.keys():
            return

        file_widgets = [
            file_widget
            for file_widget in file_groups[widget_group_name].getchildren()
            if file_widget.tag == "widget"
        ]

        for pwidget in pwidgets:
            pwidget_name = pwidget.get_element_value("name")
            for file_widget in file_widgets:
                if pwidget_name == file_widget.name:
                    assert (
                        int(pwidget.get_element_value("width")) == file_widget.width
                    ), (
                        f"{int(pwidget.get_element_value('width'))} \
!= {file_widget.width}"
                    )
                    assert (
                        int(pwidget.get_element_value("height")) == file_widget.height
                    ), (
                        f"{int(pwidget.get_element_value('height'))} \
!= {file_widget.height}"
                    )
                    assert pwidget.get_element_value("file") == file_widget.file, (
                        f"{pwidget.get_element_value('file')} != {file_widget.file}"
                    )

        LOGGER.info(f"{screen_name}.bob has been validated successfully")
