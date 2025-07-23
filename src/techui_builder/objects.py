import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Beamline:
    dom: str
    desc: str


@dataclass
class Entry:
    type: str
    desc: str | None
    file: Path
    P: str
    M: str | None
    R: str | None


@dataclass
class Component:
    name: str
    prefix: str
    service_name: str | None = field(default=None)
    desc: str | None = field(default=None)
    file: str | None = field(default=None)

    '''    def __post_init__(self):
        self.file = self.name + ".bob" if self.file is None else self.file
        
        pattern = re.compile(
            r"^"  # start of string
            r"(?=[A-Za-z0-9-]{13,16}:?[A-Za-z0-9]*\.?[A-Za-z0-9]*)"  # lookahead
            r"(?!.*--)"  # no double hyphens
            r"(?!.*:\.)"  # no colon then dot
            r"((?:[A-Za-z0-9]{2,5}-){3}[\d]*[^:]?)"  # P
            r"(?::([a-zA-Z0-9:]*))?"  # R
            r"(?:\.([a-zA-Z0-9]+))?"  # attribute
            r"$"  # end of string
        )

        match = re.match(pattern, self.prefix)
        if match:
            self.P: str = match.group(1)
            self.R: str | None = match.group(2)
            self.attribute: str | None = match.group(3)
        else:
            raise AttributeError(f"No valid PV prefix found for {self.name}.")
''
