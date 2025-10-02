# from __future__ import annotations
from __future__ import annotations

import logging
import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    StringConstraints,
    computed_field,
    field_validator,
)

LOGGER = logging.getLogger(__name__)


# Patterns:
#   long:  'bl23b'
#   short: 'b23'   (non-branch)
#   branch short: 'j23'
_DLS_PREFIX_RE = re.compile(
    r"""
            ^           # start of string
            (?=         # lookahead to ensure the following pattern matches
                [A-Za-z0-9-]{13,16} # match 13 to 16 alphanumeric characters or hyphens
                [:A-Za-z0-9]* # match zero or more colons or alphanumeric characters
                [.A-Za-z0-9]  # match a dot or alphanumeric character
            )
            (?!.*--)    # negative lookahead to ensure no double hyphens
            (?!.*:\..)  # negative lookahead to ensure no colon followed by a dot
            (           # start of capture group 1
                (?:[A-Za-z0-9]{2,5}-){3} # match 2 to 5 alphanumeric characters followed
                                    # by a hyphen, repeated 3 times
                [\d]*   # match zero or more digits
                [^:]?   # match zero or one non-colon character
            )
            (?::([a-zA-Z0-9:]*))? # match zero or one colon followed by zero or more
                                # alphanumeric characters or colons (capture group 2)
            (?:\.([a-zA-Z0-9]+))? # match zero or one dot followed by one or more
                                # alphanumeric characters (capture group 3)
            $           # end of string
        """,
    re.VERBOSE,
)
_LONG_DOM_RE = re.compile(r"^[a-z]{2}\d{2}[a-z]$")
_SHORT_DOM_RE = re.compile(r"^[a-z]\d{2}$")  # letters except 'j'
_BRANCH_SHORT_DOM_RE = re.compile(r"^[a-z]\d{2}-\d$")

BobPath = Annotated[
    str, StringConstraints(pattern=r"^(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.bob$")
]
# Must contain at least one $(NAME) macro
MacroString = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_:\-./\s\$\(\)]+$"),
]
EntryType = Literal["embedded", "related"]


class Beamline(BaseModel):
    dom: str = Field(
        description="e.g. 'bl23b' (long), 'b23' (short), or 'j23' (branch short)"
    )
    desc: str

    @field_validator("dom")
    @classmethod
    def normalize_dom(cls, v: str) -> str:
        v = v.strip().lower()
        if _LONG_DOM_RE.fullmatch(v):
            # already long: bl23b
            return v
        if _SHORT_DOM_RE.fullmatch(v):
            # e.g. b23 -> bl23b
            return f"bl{v[1:3]}{v[0]}"
        if _BRANCH_SHORT_DOM_RE.fullmatch(v):
            # e.g. j23 -> bl23j
            return f"bl{v[1:3]}j"
        raise ValueError("Invalid dom. Expected long or short")

    @computed_field
    @property
    def long_dom(self) -> str:
        # dom is normalized to long already
        return self.dom

    @computed_field
    @property
    def short_dom(self) -> str:
        # Convert long -> short form: bl23b -> b23, bl23j -> j23
        # long form is 'bl' + digits + tail-letter
        return f"{self.dom[4]}{self.dom[2:4]}"


class Component(BaseModel):
    desc: str | None = None
    prefix: str
    extras: list[str] | None = None
    file: str | None = None

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, v: str) -> str:
        if not _DLS_PREFIX_RE.match(v):
            raise ValueError(f"prefix '{v}' does not match DLS prefix pattern")
        return v

    @field_validator("extras", mode="before")
    @classmethod
    def _normalize_extras(cls, v):
        return [] if v is None else v

    @field_validator("extras", mode="after")
    @classmethod
    def _check_extras(cls, v: list[str]) -> list[str]:
        for p in v:
            if not _DLS_PREFIX_RE.match(p):
                raise ValueError(f"extras item '{p}' does not match DLS prefix pattern")
        # ensure unique (schema enforces too; this is a runtime guarantee)
        if len(set(v)) != len(v):
            raise ValueError("extras must contain unique items")
        return v

    @computed_field
    @property
    def P(self) -> str | None:
        match = re.match(_DLS_PREFIX_RE, self.prefix)
        if match:
            return match.group(1)

    @computed_field
    @property
    def R(self) -> str | None:
        match = re.match(_DLS_PREFIX_RE, self.prefix)
        if match:
            return match.group(2)

    @computed_field
    @property
    def attribute(self) -> str | None:
        match = re.match(_DLS_PREFIX_RE, self.prefix)
        if match:
            return match.group(3)


class TechUi(BaseModel):
    beamline: Beamline
    components: dict[str, Component]


class GuiComponentEntry(BaseModel):
    file: BobPath
    prefix: MacroString
    type: EntryType


class GuiComponents(RootModel[dict[str, GuiComponentEntry]]):
    pass
