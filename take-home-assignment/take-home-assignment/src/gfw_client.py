"""
Thin wrapper around the Global Fishing Watch v3 REST API.

Only wraps the two endpoints this pipeline actually uses -- Vessels
search and Events -- both of which are exercised with confirmed
request/response shapes straight from GFW's own quick-start docs.
Handles auth, retry/backoff on rate limits and transient server
errors, and pagination.
"""

import logging
import time
from typing import Any, Optional

import requests

from config import GFW_API_TOKEN, GFW_BASE_URL

logger = logging.getLogger(__name__)


class GFWAPIError(Exception):
    """Raised when the GFW API returns an error we won't retry past."""


class GFWClient:
    def __init__(self, token: Optional[str] = None, max_retries: int = 5, timeout: int = 60):
        self.token = token or GFW_API_TOKEN
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    # -- low-level request handling ---------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{GFW_BASE_URL}{path}"
        attempt = 0

        while True:
            attempt += 1
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
            except requests.exceptions.Timeout:
                self._retry_or_raise(attempt, f"Timed out calling {url}")
                continue
            except requests.exceptions.ConnectionError as exc:
                self._retry_or_raise(attempt, f"Connection error calling {url}: {exc}")
                continue

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                # GFW rate limits (some endpoints allow only one concurrent
                # report per user). Respect Retry-After when present.
                wait = float(resp.headers.get("Retry-After", self._backoff(attempt)))
                self._retry_or_raise(attempt, f"429 rate limited on {url}", wait=wait)
                continue

            if resp.status_code == 524:
                # Gateway timeout on long-running requests. Not expected on
                # search/events, but handled defensively -- retry with backoff.
                self._retry_or_raise(attempt, f"524 gateway timeout on {url}")
                continue

            if 500 <= resp.status_code < 600:
                self._retry_or_raise(attempt, f"{resp.status_code} server error on {url}")
                continue

            # Any other 4xx (400, 401, 403, 404, 422 ...) is not retried --
            # it means the request itself is wrong, not that the server is busy.
            raise GFWAPIError(f"{resp.status_code} from {url}: {resp.text[:500]}")

    def _retry_or_raise(self, attempt: int, message: str, wait: Optional[float] = None) -> None:
        if attempt > self.max_retries:
            raise GFWAPIError(f"{message} (gave up after {attempt} attempts)")
        wait = wait if wait is not None else self._backoff(attempt)
        logger.warning("%s -- retrying in %.1fs (attempt %d/%d)", message, wait, attempt, self.max_retries)
        time.sleep(wait)

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(2**attempt, 30)  # 2, 4, 8, 16, 30, 30, ... capped at 30s

    # -- confirmed endpoints -------------------------------------------------

    def search_vessels(self, query: str, dataset: str, limit: int = 50) -> dict:
        """GET /v3/vessels/search -- resolve a name/IMO/MMSI query to vessel records.

        No offset here: unlike /v3/events, this endpoint's schema doesn't
        define an offset property at all -- passing one gets a 422
        ("property offset should not exist"), confirmed against the live
        API. Search queries typically match a small number of vessels
        anyway, so this pulls up to `limit` in one call rather than
        paginating; extract_vessels.py logs a warning if `total` in the
        response is larger than what came back, so a truncation would be
        visible rather than silent.
        """
        params = {
            "query": query,
            "datasets[0]": dataset,
            "limit": limit,
        }
        return self._request("GET", "/v3/vessels/search", params=params)

    def get_events(
        self,
        vessel_ids: list[str],
        dataset: str,
        start_date: str,
        end_date: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """GET /v3/events -- fishing events for a set of internal vessel ids."""
        params: list[tuple[str, Any]] = [
            ("datasets[0]", dataset),
            ("start-date", start_date),
            ("end-date", end_date),
            ("limit", limit),
            ("offset", offset),
        ]
        for i, vessel_id in enumerate(vessel_ids):
            params.append((f"vessels[{i}]", vessel_id))
        return self._request("GET", "/v3/events", params=params)

    # -- pagination -----------------------------------------------------------

    def paginate(self, fetch_page, page_size: int = 50) -> list[dict]:
        """Drive limit/offset pagination against any of the calls above.

        fetch_page(offset, limit) -> raw response dict for that page.
        Stops when nextOffset is missing, a page comes back empty, or
        we've collected `total` records (whichever comes first).
        """
        offset = 0
        all_entries: list[dict] = []

        while True:
            page = fetch_page(offset=offset, limit=page_size)
            entries = page.get("entries", [])
            all_entries.extend(entries)

            total = page.get("total", len(all_entries))
            next_offset = page.get("nextOffset")
            logger.info("Fetched %d/%s records (offset=%d)", len(all_entries), total, offset)

            if not entries or next_offset is None or len(all_entries) >= total:
                break
            offset = next_offset

        return all_entries
