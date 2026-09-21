"""Fetching remote .bob screens over http(s)."""

import logging
from dataclasses import dataclass, field
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

logger_ = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10


def download_url(url: str) -> bytes:
    """Download the contents of a URL."""
    with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


@dataclass
class ScreenFetcher:
    """Fetches remote screens."""

    _screens: dict[str, bytes] = field(default_factory=dict)
    _unreachable_hosts: dict[str, OSError] = field(default_factory=dict)

    def fetch(self, url: str) -> bytes:
        """Fetch a screen, raising HTTPError if missing or OSError if unreachable."""
        if url in self._screens:
            return self._screens[url]

        # Don't wait for a timeout on every screen from a host that is down
        host = urlparse(url).netloc
        if host in self._unreachable_hosts:
            raise self._unreachable_hosts[host]

        try:
            screen = download_url(url)
        except HTTPError as e:
            logger_.warning(f"Could not fetch {url}: {e}")
            raise
        except OSError as e:
            logger_.warning(f"Could not reach {host}, not crawling its screens: {e}")
            self._unreachable_hosts[host] = e
            raise

        self._screens[url] = screen
        return screen
