import logging
import re
from dataclasses import dataclass, field

LOGGER = logging.getLogger(__name__)

long_dom_re = "^([a-z]{2})([0-9]{2})([a-z])$"
short_dom_re = "^([a-z])([0-9]{2})$"
branch_short_dom_re = "^([a-z])([0-9]{2})-([0-9])$"


@dataclass
class Beamline:
    dom: str
    desc: str
    short_dom: str = field(init=False)
    long_dom: str = field(init=False)

    def __post_init__(self):
        if re.match(long_dom_re, self.dom):
            LOGGER.debug(f"DOM '{self.dom}' matches long DOM format")
            self.long_dom = self.dom
            self.short_dom = f"{self.dom[4]}{self.dom[2:4]}"
        elif re.match(short_dom_re, self.dom):
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


@dataclass
class Entity:
    type: str
    desc: str | None
    P: str
    M: str | None
    R: str | None


@dataclass
class Component:
    name: str
    prefix: str
    desc: str | None = field(default=None)
    file: str | None = field(default=None)
    extras: list[str] | None = field(default=None)

    def __post_init__(self):
        self.file = self.name + ".bob" if self.file is None else self.file
        self._extract_p_and_r()

    def __repr__(self) -> str:
        return f"Component(name={self.name}, desc={self.desc}, \
prefix={self.P}, suffix={self.R}, filename={self.file})"

    def _extract_p_and_r(self):
        pattern = re.compile(
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

        match = re.match(pattern, self.prefix)
        if match:
            self.P: str = match.group(1)
            self.R: str | None = match.group(2)
            # TODO: Is this needed?
            self.attribute: str | None = match.group(3)
        else:
            raise AttributeError(f"No valid PV prefix found for {self.name}.")
