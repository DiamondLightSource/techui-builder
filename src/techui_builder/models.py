from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field, field_validator

LOGGER = logging.getLogger(__name__)

_DLS_PREFIX_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z]-[A-Z]{2}-[A-Z0-9]+-\d{2}$")
_LONG_DOM_RE = re.compile(r"^([a-z]{2})([0-9]{2})([a-z])$")
_SHORT_DOM_RE = re.compile(r"^([a-z])([0-9]{2})$")
branch_short_dom_re = "^([a-z])([0-9]{2})-([0-9])$"


class Beamline(BaseModel):
    dom: str = Field(description="e.g. 'bl23b'")
    desc: str
    short_dom: str
    long_dom: str

    def __post_init__(self) -> str:
        if re.match(_LONG_DOM_RE, self.dom):
            LOGGER.debug(f"DOM '{self.dom}' matches long DOM format")
            self.long_dom = self.dom
            self.short_dom = f"{self.dom[4]}{self.dom[2:4]}"
        elif re.match(_SHORT_DOM_RE, self.dom):
            LOGGER.debug(f"DOM '{self.dom}' matches short DOM format")
            self.long_dom = f"bl{self.dom[1:3]}{self.dom[0]}"
            self.short_dom = self.dom
        elif re.match(branch_short_dom_re, self.dom):
            LOGGER.debug(f"DOM '{self.dom}' matches branch short DOM format")
            self.long_dom = f"bl{self.dom[1:3]}j"
            self.short_dom = f"j{self.dom[1:3]}"
        else:
            LOGGER.critical("Valid beamline DOM not found in create_gui.yaml")
            exit()

    @field_validator("dom")
    @classmethod
    def _check_dom(cls, v: str) -> str:
        if not _SHORT_DOM_RE.match(v):
            raise ValueError("dom must match ^[a-z]{2}\\d{2}[a-z]$")
        return v


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
