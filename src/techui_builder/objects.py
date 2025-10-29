import logging
import re
from dataclasses import dataclass, field

LOGGER = logging.getLogger(__name__)

long_dom_re = "^([a-zA-Z]{2})([0-9]{2})([a-zA-Z])$"
short_dom_re = "^([a-zA-Z])([0-9]{2})(-[0-9]{1})?$"


@dataclass
class Beamline:
    long_dom: str
    short_dom: str
    desc: str

    def __post_init__(self):
        if re.match(long_dom_re, self.long_dom) and (
            re.match(short_dom_re, self.short_dom)
        ):
            LOGGER.debug("Valid beamline domain formats")
        else:
            LOGGER.critical("Valid beamline DOM not found in techui.yaml")
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
                [A-Za-z0-9*?\[\]-]{2,16} # match 13-16 alphanumeric chars,-/wildcards
                [:A-Za-z0-9*?[\]]* # match >=0 colons or alphanumeric chars/wildcards
                [.A-Za-z0-9*?[\]]  # match a dot or alphanumeric chars or wildcards
            )
            (?!.*--)    # negative lookahead to ensure no double hyphens
            (?!.*:\..)  # negative lookahead to ensure no colon followed by a dot
            (           # start of capture group 1
                (?:[A-Za-z0-9*?,\[\]-])* # match 2 to 5 alphanumeric characters followed
                                    # by a hyphen, repeated 3 times
                [\d*]*   # match zero or more digits
                [^:]?   # match zero or one non-colon character
            )
            (?::([a-zA-Z0-9*:]*))? # match zero or one colon followed by zero or more
                                # alphanumeric characters or colons (capture group 2)
            (?:\.([a-zA-Z0-9*]+))? # match zero or one dot followed by one or more
                                # alphanumeric characters (capture group 3)
            $           # end of string
        """,
            re.VERBOSE | re.UNICODE,
        )

        match = re.match(pattern, self.prefix)
        if match:
            self.P: str = match.group(1)
            self.R: str | None = match.group(2)
            # TODO: Is this needed?
            self.attribute: str | None = match.group(3)
        else:
            raise AttributeError(f"No valid PV prefix found for {self.name}.")
