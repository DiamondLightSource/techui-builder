"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by poetry-dynamic-versioning
"""

from importlib.metadata import version

from phoebus_guibuilder.datatypes import Beamline, Component, Entry

__version__ = version("phoebus_guibuilder")

__all__ = ["__version__", "Beamline", "Component", "Entry"]
