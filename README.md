[![CI](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/techui-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/techui-builder)
[![PyPI](https://img.shields.io/pypi/v/techui-builder.svg)](https://pypi.org/project/techui-builder)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# techui_builder

A package for building Phoebus GUIs

Techui-builder is a module for building and organising phoebus gui screens using a builder-ibek yaml description of an IOC, with a user created create_gui.yaml file containing a description of the screens the user wants to create.

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
1. Clone this module with the `--recursive` flag to pull in [techui-support](git@github.com:DiamondLightSource/techui-support.git). 
2. Open the project using VSCode.
3. Reopen the project in a container. Make sure you are using the vscode extension: Dev Containers by Microsoft.
    
## Setting Up

> [!WARNING]
> This module currently only works for `example-synoptic/bl23b-services` - use this directory file structure as a guideline.

1. Add the beamline `ixx-services` repo to your VSCode workspace, ensuring each IOC service has been converted to the [ibek](git@github.com:epics-containers/ibek.git) format:
    ```
    |-- ixx-services
    |   |-- services
    |   |   |-- $(dom)-my-device-01
    |   |   |   |-- config
    |   |   |   |   |-- ioc.yaml
    ```
2. Create your handmade synoptic screen in Phoebus and place in `ixx-services/src-bob/$(dom)-synoptic-src.bob`.
3. Amend any references to `example-synoptic` with the path to your local `ixx-services` - [generate_synoptic.py](example-synoptic/generate_synoptic.py) and [generate.py](src/techui_builder/generate.py).
4. Construct a `create_gui.yaml` file at the root of `ixx-services` containing all the components from the services:

    ```
    beamline:
        dom: {beamline name}
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

## Generating Synoptic
> [!WARNING]
> Again, this is hardcoded to work for `example-synoptic/bl23b-services` so amend filepaths accordingly.

`$ python example-synoptic/generate_synoptic.py`

This generates the filled, top level blxxx-synoptic.bob and all component screens inside `ixx-services/services/data`.

## Viewing the Synoptic

```
$ module load phoebus
$ phoebus.sh -resource /path/to/blxxx-synoptic.bob
```
