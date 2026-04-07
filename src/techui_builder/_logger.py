import logging
from dataclasses import dataclass, field

from rich.logging import RichHandler


@dataclass
class Logger:
    level: str = field(default="INFO")

    handler = RichHandler(omit_repeated_times=False, markup=True)

    def __post_init__(self):
        logging.basicConfig(
            level=self.level.upper(),
            format="%(message)s",
            handlers=[self.handler],
        )
