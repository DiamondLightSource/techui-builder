[![CI](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/techui-builder/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/techui-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/techui-builder)
[![PyPI](https://img.shields.io/pypi/v/techui-builder.svg)](https://pypi.org/project/techui-builder)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# techui_builder

A package for building Phoebus GUIs

Techui-builder is a module for building and organising Phoebus CS-Studio `.bob` screens from a `techui.yaml` description of a beamline's IOC services. It also can auto-generate a synoptic `index.bob` showing devices laid out along the beam pipe and vacuum pipe, eliminating the need to hand-craft the overview screen in Phoebus.

The `.bob` file screens are intended to be served to [Daedalus](https://github.com/DiamondLightSource/daedalus), Diamond's web-based control system UI.

Source          | <https://github.com/DiamondLightSource/techui-builder>
:---:           | :---:
PyPI            | `pip install techui-builder`
Releases        | <https://github.com/DiamondLightSource/techui-builder/releases>

The process to use this module goes as follows (WIP): 

## Requirements

1. Docker
2. VSCode
3. CS-Studio (Phoebus)

## Setup

1. Clone this module with the `--recursive` flag to pull in [techui-support](https://github.com/DiamondLightSource/techui-support) for the associated bob file templates and SVG symbols.

2. Open the project using VSCode and reopen in the dev container when prompted. Make sure you are using the VSCode extension: Dev Containers by Microsoft.

3. Clone your beamline `ixx-services` repo to the root of this project, ensuring each IOC service has been converted to the ibek format.


## Writing a `techui.yaml` from scratch

1. Construct a `techui.yaml` file inside `ixx-services/synoptic` containing all the components from the services:

    ```
    beamline:
        location: {e.g. ixx, ixx-1}
        domain: {e.g. blxxi}
        desc: {beamline description}
        url: {e.g. ixx-opis.diamond.ac.uk}

    beam_pipe:
        {component name, e.g. S1}:
            label: {component description}
            prefix: {PV prefix}
            icon_type: {e.g. slits}
            extras: 
                - {extra prefix 1}
                - {extra prefix 2}

    vacuum_pipe:
        {component name, e.g. img01}:
            label: {e.g. IMG 01}
            prefix: {PV prefix}
            icon_type: {e.g. img}

    ```
    > [!NOTE] 
    > `extras` is optional, but allows any embedded screen to be added to a summary screen

    Devices are rendered left-to-right in the order they appear in the file.

    For devices not on the beam/vacuum pipe (e.g. detectors, sample environments etc), declare they under `components`. These generate `.bob` screens but do not appear on the synoptic overview.

    > [!NOTE]
    > If you already have a hand-crafted `index.bob` and do not define `beam_pipe` or `vacuum_pipe` in `techui.yaml`, it will be preserved as is. Defining either section will auto-generate and overwrite `index.bob`.

## Icon Type Naming Convention ##

`icon_type` values must use underscores. The corresponding SVG in `techui-support/symbols/` must use hyphens. For example:

| `icon_type` | SVG file
| ----------- | -----------
| `ion_pump`  | `ion-pump.svg`
| `camera`    | `camera.svg`

See the techui-support README for the full list of available symbols.

## Schema Generation ## 

1. Run this command to locally generate a schema, which can be used for validation testing

    ```$ techui-builder schema```

    Add the following at the top of the `techui.yaml` to validate it against a schema
    
    ```# yaml-language-server: $schema=/path/to/techui.schema.yml```
    
    where the path can be the dev container workspace, or a [released asset in the GitHub repo](https://github.com/DiamondLightSource/techui-builder/releases/download/0.3.0a1/techui.schema.yml).

## Generating the Synoptic

`$ techui-builder generate /path/to/synoptic/techui.yaml`

This populates `index.bob` and individual component screens inside `ixx-services/synoptic`.

Output files are written to `ixx-services/synoptic/`.

## Generating the JsonMap

`$ techui-builder generate-jsonmap /path/to/synoptic/index.bob`

This populates `JsonMap.json` with the tree of component screens inside `ixx-services/synoptic/index.bob`. This is used for Daedalus navigation to create the tree view in the side panel.

Output files are written to `ixx-services/synoptic/`.

## Generating the Status PV database file

`$ techui-builder status /path/to/synoptic/techui.yaml`

This populates `config/status.db` with the status PVs of components inside `ixx-services/synoptic/techui.yaml`.

## Viewing the Synoptic

In a terminal outside of the container:
```
$ module load phoebus
$ phoebus.sh -resource /path/to/opis/index.bob
```
