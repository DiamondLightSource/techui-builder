import pprint
import re
from dataclasses import dataclass
from typing import Dict

import yaml

pp = pprint.PrettyPrinter()


@dataclass
class Beamline:
    dom: str
    desc: str


@dataclass
class Component:
    name: str
    type: str
    desc: str
    prefix: str
    filename: str | None = None


components: list[Component] = []

with open("create_gui.yaml", "r") as f:
    conf = yaml.safe_load(f)

    bl: dict[str, str] = conf["beamline"]
    comps: dict[str, dict[str, str]] = conf["components"]

    beamline = Beamline(**bl)

    for key, comp in comps.items():
        components.append(Component(key, **comp))

print("BEAMLINE:")
pp.pprint(beamline)

print("")
print("COMPONENTS")
pp.pprint(components)


pattern = r"^(.*?):([A-Z]+)\.([A-Z]+)$"

for component in components:
    prefix = component.prefix

    print(prefix)

    match = re.match(pattern, prefix)
    if match:
        prefix = match.group(1)
        suffix = match.group(2)
        sub_group = match.group(3)
        print(f"Prefix: {prefix}")
        print(f"Suffix: {suffix}")
        print(f"Sub Group: {sub_group}")
    else:
        print("No match found")
