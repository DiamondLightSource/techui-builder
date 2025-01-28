# Import dependencies
import os
import re
import yaml
from dataclasses import dataclass

# Check beamline and type in create_gui.yaml  
#Example create_gui output:
from guibuilder import Beamline, Component

beamline = Beamline(dom="p47", desc="Test Beamline")

component = Component(name="motor", desc= "generic motor", prefix= "BL47P-MO-MAP-01:STAGE", filename=None)

@dataclass
class Entry:
    type: str
    DESC: str | None
    P: str
    M: str | None
    R: str | None


# Check associated ioc_yaml in the right beamline services for $(P)$(M)
#find ioc_yaml file based on type of component - DCM (MO), Camera - (CAM/DET)
services_directory = beamline.dom + "-services/services"  # Will be changed, probably made relative to actual directory i.e. "./services" or absolute paths.
path = f"/dls/science/users/uns32131/{services_directory}"
files = os.listdir(path)

for file in files:
    print(file)


# Attempting to match the prefix to the files in the services directory
pattern = "^(.*)-(.*)-(.*)"
prefix = re.match(pattern, component.prefix)
iocs_yaml = []

for file in files: 
    match = re.match(pattern, file)
    if match:
        if match.group(1) == prefix.group(1).lower():
            print(match.group(1))
            print(match.group(2))
            iocs_yaml.append(f"{path}/{file}/config/ioc.yaml") 

print(iocs_yaml)

# Matching  the entities with the required prefix and taking important data 
for ioc_yaml in iocs_yaml:
    with open(ioc_yaml, "r") as ioc:
        conf = yaml.safe_load(ioc)

        print(conf)

        entities: list[dict[str,str]] = conf["entities"]
        valid_entities: list[dict[str,str]] = []

        for entity in entities:
            if 'P' in entity.keys() and entity['P'] == component.prefix: # the suffix could be M, could be R
                valid_entities.append(entity)



print("\n\n\n")
print(valid_entities)

# Make objects out of the valid entities

entrys = [Entry(type= valid_entry["type"], DESC = None, P = valid_entry["P"], M = None, R = None) for valid_entry in valid_entities]

print(entrys)
# ioc_yaml = os.path.join(file, "/config/ioc.yaml")

# Match that to gui_map file in BLGui
gui_map = "/dls/science/users/uns32131/BLGui/BLGuiApp/opi/bob/gui_map.yaml"

with open(gui_map, "r") as map:
    conf = yaml.safe_load(map)

    for entry in entrys:
        print(entry.type)
        if conf[entry.type]:
            print(conf[entry.type]["file"]) # First find the correct file, and then format the prefix and suffix for the macro
            # create a copy of the file, and replace the required macros
            # return the file to guibuilder
        else:
            print("No BOB available")


# Output required screen