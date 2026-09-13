from __future__ import annotations

import time

import requests

from morning.config import REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
)


def get(url: str, retries: int = 3, delay: float = REQUEST_DELAY_SECONDS, **kwargs) -> requests.Response | None:
    """GET with retry/backoff. Returns None on 404 (treated as "no data"), raises on other failures."""
    last_error = None
    for attempt in range(retries):
        try:
            resp = _session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(delay * (attempt + 1))
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code == 200:
            time.sleep(delay)
            return resp
        last_error = RuntimeError(f"HTTP {resp.status_code} for {url}")
        time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_error}")
