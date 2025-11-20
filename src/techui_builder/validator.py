import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

LOGGER = logging.getLogger(__name__)


@dataclass
class Validator:
    bobs: list[Path]
    validate: list[Path] = field(default_factory=list, init=False, repr=False)

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
                self.validate.append(bob_path)
