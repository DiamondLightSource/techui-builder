# from __future__ import annotations
from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field, computed_field, field_validator

# import re

# from pydantic import BaseModel, Field, PrivateAttr, computed_field, field_validator

LOGGER = logging.getLogger(__name__)

_DLS_PREFIX_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z]-[A-Z]{2}-[A-Z0-9]+-\d{2}$")
# _LONG_DOM_RE = re.compile(r"^([a-z]{2})([0-9]{2})([a-z])$")
# _SHORT_DOM_RE = re.compile(r"^([a-z])([0-9]{2})$")
# branch_short_dom_re = "^([a-z])([0-9]{2})-([0-9])$"


# Patterns:
#   long:  'bl23b'
#   short: 'b23'   (non-branch)
#   branch short: 'j23'
_LONG_DOM_RE = re.compile(r"^[a-z]{2}\d{2}[a-z]$")
_SHORT_DOM_RE = re.compile(r"^[a-ik-z]\d{2}$")  # letters except 'j'
_BRANCH_SHORT_DOM_RE = re.compile(r"^[a-z]\d{2}$")


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


class CreateGui(BaseModel):
    beamline: Beamline
    components: dict[str, Component]

    @field_validator("components")
    @classmethod
    def _check_component_keys(cls, comps: dict[str, Component]) -> dict[str, Component]:
        for k in comps.keys():
            if not re.match(r"^[A-Z0-9_]+$", k):
                raise ValueError(f"component key '{k}' must match ^[A-Z0-9_]+$")
        return comps
