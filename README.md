[![CI](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/techui-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/techui-builder)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# techui_builder

A package for building GUIs

Techui-builder is a module for building and organising phoebus gui screens using a builder-ibek yaml description of an IOC, with a user created create_gui.yaml file containing a description of the screens the user wants to create.

Source          | <https://github.com/DiamondLightSource/techui-builder>
:---:           | :---:
Docker          | `docker run ghcr.io/diamondlightsource/techui-builder:latest`
Releases        | <https://github.com/DiamondLightSource/techui-builder/releases>

The process to use this module goes as follows (WIP): 

# Requirements
    1. Docker
    2. VSCode

# Starting the module
    1. Recursively pull the project ensuring you pull submodules too. 
    1. Open the project using vscode
    2. Reopen the project in a container. Make sure you are using the vscode extension: Dev Containers by Microsoft.
    
# Running the module
    1. With your ioc.yaml file in the folder format for services at diamond, as shown in the example-synoptics folder
    2. Create a create_gui.yaml file as shown in the example folder of your beamline with a description as follows:

    ```
    beamline:
        dom: {beamline name}
        desc: {beamline description}

    components:
        {component name}:
            desc: {component description}
            prefix: {PV prefix}
            service_name: {name of kubernetes service}
    ```
    3. Create your handmade synoptic screen and place in folder ./example-synoptic/src-bob

# Running techui-builder
    1. Run generate_synoptic.py in the example-synoptic folder
