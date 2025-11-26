from lxml import objectify
from lxml.objectify import ObjectifiedElement


def read_bob(path):
    # Read the bob file
    tree = objectify.parse(path)

    # Find the root tag (in this case: <display version="2.0.0">)
    root = tree.getroot()

    widgets = get_widgets(root)

    return tree, widgets


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
