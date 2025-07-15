"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by poetry-dynamic-versioning
"""

from techui_builder.builder import Builder

from ._version import __version__

__all__ = [
    "__version__",
    "Builder",
]
