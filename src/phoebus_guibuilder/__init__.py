"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by poetry-dynamic-versioning
"""

from importlib.metadata import version

__version__ = version("phoebus_guibuilder")

__all__ = ["__version__"]
