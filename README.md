[![CI](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/techui-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/techui-builder)
[![PyPI](https://img.shields.io/pypi/v/techui-builder.svg)](https://pypi.org/project/techui-builder)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# techui_builder

A package for building Phoebus GUIs

Techui-builder is a module for building and organising phoebus gui screens using a builder-ibek yaml description of an IOC, with a user created techui.yaml file containing a description of the screens the user wants to create.

Source          | <https://github.com/DiamondLightSource/techui-builder>
:---:           | :---:
PyPI            | `pip install techui-builder`
Releases        | <https://github.com/DiamondLightSource/techui-builder/releases>

The process to use this module goes as follows (WIP): 

## Requirements
1. Docker
2. VSCode
3. CS-Studio (Phoebus)

## Installation
1. Clone this module with the `--recursive` flag to pull in [techui-support](git@github.com:DiamondLightSource/techui-support.git) for the associated bob files. 
2. Open the project using VSCode.
3. Reopen the project in a container. Make sure you are using the VSCode extension: Dev Containers by Microsoft.
    
## Setting Up

1. Clone the beamline `ixx-services` repo to the root of this project, ensuring each IOC service has been converted to the [ibek](git@github.com:epics-containers/ibek.git) format.
1. Create your handmade synoptic overview screen in Phoebus and place inside `ixx-services/synoptic/index.bob`.
1. Construct a `techui.yaml` file inside `ixx-services/synoptic` containing all the components from the services:

    ```
    beamline:
        short_dom: {e.g. b23, b01-1}
        long_dom: {e.g. bl23b}
        desc: {beamline description}

    components:
        {component name}:
            desc: {component description}
            prefix: {PV prefix}
            extras: 
                - {extra prefix 1}
                - {extra prefix 2}
    ```
    > [!NOTE] 
    > `extras` is optional, but allows any embedded screen to be added to make a summary screen e.g. combining all imgs, pirgs and ionps associated with a vacuum space.
1. Run this command to locally generate a schema, which can be used for validation testing

    ```$ techui-builder --schema```

    Add the following at the top of the `techui.yaml` to validate it against a schema
    
    ```# yaml-language-server: $schema=/path/to/techui.schema.yml```
    
    where the path can be the dev container workspace, or a [released asset in the GitHub repo](https://github.com/DiamondLightSource/techui-builder/releases/download/0.3.0a1/techui.schema.yml).

## Generating the Synoptic

`$ techui-builder /path/to/synoptic/techui.yaml`

This populates `index.bob` and individual component screens inside `ixx-services/synoptic`.

## Viewing the Synoptic

In a terminal outside of the container:
```
$ module load phoebus
$ phoebus.sh -resource /path/to/opis/index.bob
```
