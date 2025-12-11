import logging
import os
from pathlib import Path

from lxml import objectify
from lxml.etree import _ElementTree
from lxml.objectify import ObjectifiedElement


def read_bob(path):
    # Read the bob file
    tree = objectify.parse(path)

    # Find the root tag (in this case: <display version="2.0.0">)
    root = tree.getroot()

    widgets = get_widgets(root)

    return tree, widgets


def write_bob(tree: _ElementTree[ObjectifiedElement], filename: Path):
    # Check if data/ dir exists and if not, make it
    data_dir = filename.parent
    if not data_dir.exists():
        os.mkdir(data_dir)

    # Remove any unnecessary xmlns:py and py:pytype metadata from tags
    objectify.deannotate(tree, cleanup_namespaces=True)

    tree.write(
        filename,
        pretty_print=True,
        encoding="utf-8",
        xml_declaration=True,
    )
    logger_ = logging.getLogger()
    logger_.debug(f"Screen filled for {filename}")


def get_widgets(root: ObjectifiedElement):
    widgets: dict[str, ObjectifiedElement] = {}
    # Loop over objects in the xml
    # i.e. every tag below <display version="2.0.0">
    # but not any nested tags below them
    for child in root.iterchildren():
        # If widget is a symbol (i.e. a component)
        if child.tag == "widget" and child.get("type", default=None) in [
            "symbol",
            "group",
        ]:
            name = child.name.text
            assert name is not None
            widgets[name] = child

    return widgets
