import logging
import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    StringConstraints,
    computed_field,
    field_validator,
)

LOGGER = logging.getLogger(__name__)


# Patterns:
#   long:  'bl23b'
#   short: 'b23', 'ixx-1'


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
_LONG_DOM_RE = re.compile(r"^[a-zA-Z]{2}\d{2}[a-zA-Z]$")
_SHORT_DOM_RE = re.compile(r"^[a-zA-Z]{1}\d{2}(-[0-9]{1})?$")


class Beamline(BaseModel):
    short_dom: str = Field(description="Short BL domain e.g. b23, ixx-1")
    long_dom: str = Field(description="Full BL domain e.g. bl23b")
    desc: str = Field(description="Description")
    model_config = ConfigDict(extra="forbid")

    @field_validator("short_dom")
    @classmethod
    def normalize_short_dom(cls, v: str) -> str:
        v = v.strip().lower()

        if _SHORT_DOM_RE.fullmatch(v):
            # e.g. b23 -> bl23b
            return v

        raise ValueError("Invalid short dom.")

    @field_validator("long_dom")
    @classmethod
    def normalize_long_dom(cls, v: str) -> str:
        v = v.strip().lower()
        if _LONG_DOM_RE.fullmatch(v):
            # already long: bl23b
            return v

        raise ValueError("Invalid long dom.")


class Component(BaseModel):
    prefix: str
    desc: str | None = None
    extras: list[str] | None = None
    file: str | None = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, v: str) -> str:
        if not _DLS_PREFIX_RE.match(v):
            raise ValueError(f"prefix '{v}' does not match DLS prefix pattern")
        return v

    @field_validator("extras")
    @classmethod
    def _check_extras(cls, v: list[str]) -> list[str]:
        for p in v:
            if not _DLS_PREFIX_RE.match(p):
                raise ValueError(f"extras item '{p}' does not match DLS prefix pattern")
        # ensure unique (schema enforces too)
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
    model_config = ConfigDict(extra="forbid")


"""
techui_support mapping models
"""

BobPath = Annotated[
    str, StringConstraints(pattern=r"^(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.bob$")
]
# Must contain at least one $(NAME) macro
MacroString = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_:\-./\s\$\(\)]+$"),
]
ScreenType = Literal["embedded", "related"]


class GuiComponentEntry(BaseModel):
    file: BobPath
    prefix: MacroString
    type: ScreenType
    model_config = ConfigDict(extra="forbid")


GuiComponentUnion = list[GuiComponentEntry] | GuiComponentEntry


class GuiComponents(RootModel[dict[str, GuiComponentUnion]]):
    pass


class Entity(BaseModel):
    type: str
    P: str
    desc: str | None = None
    M: str | None
    R: str | None
