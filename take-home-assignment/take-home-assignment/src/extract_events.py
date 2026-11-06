"""
Extract fishing events for a set of vessel ids from the GFW Events
API, and land them as raw JSON.

Designed as the second step in a Step Functions state machine: it
expects event["vessel_ids"] to be passed in from the vessels
extraction step, so the two Lambdas share one discovery pass instead
of each re-querying vessel identity. When run standalone (e.g.
`python extract_events.py`), it resolves vessel ids itself so it's
still testable end-to-end without an orchestrator.

The extraction window is incremental (see compute_extraction_window
below), not a fixed date range -- each run picks up where the last
successful run left off, bounded by a publication-lag buffer. This
also structurally prevents the duplicate-event issue documented in
the README's Troubleshooting section: two runs close together compute
the same window and the second one gets None back, extracting nothing,
rather than re-fetching (and re-landing) the same events.
fact_fishing_event.sql's dedup stays in place regardless, as a safety
net for anything that slips past this, not a replacement for it.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from config import (
    EVENTS_INITIAL_LOOKBACK_DAYS,
    EVENTS_LAG_DAYS,
    EVENTS_WATERMARK_KEY,
    FISHING_EVENTS_DATASET,
)
from extract_vessels import extract_vessels, vessel_ids_from_records
from gfw_client import GFWClient
from storage import read_watermark, write_raw_records, write_watermark

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_extraction_window(now: Optional[datetime] = None) -> Optional[tuple[str, str]]:
    """Returns (start_date, end_date) as YYYY-MM-DD strings for this
    run's extraction window, or None if there's nothing new to extract.

    end_date always stays EVENTS_LAG_DAYS behind `now`, to respect
    GFW's own publication lag. start_date comes from the persisted
    watermark (the end_date of the last successful run), or
    EVENTS_INITIAL_LOOKBACK_DAYS back if no watermark exists yet (the
    very first run). Returns None instead of a window when start_date
    would land on or after end_date -- e.g. two runs close together on
    the same day -- so a rerun naturally does nothing instead of
    re-fetching events already extracted.
    """
    now = now or datetime.now(timezone.utc)
    end_date = (now - timedelta(days=EVENTS_LAG_DAYS)).date()

    watermark = read_watermark(EVENTS_WATERMARK_KEY)
    if watermark:
        start_date = date.fromisoformat(watermark)
    else:
        logger.info(
            "No watermark found -- this looks like the first run, looking back %d days",
            EVENTS_INITIAL_LOOKBACK_DAYS,
        )
        start_date = end_date - timedelta(days=EVENTS_INITIAL_LOOKBACK_DAYS)

    if start_date >= end_date:
        logger.info(
            "Nothing new to extract: watermark (%s) is already at or past the lag-adjusted end date (%s)",
            start_date, end_date,
        )
        return None

    return start_date.isoformat(), end_date.isoformat()


def extract_events(client: GFWClient, vessel_ids: list[str], start_date: str, end_date: str) -> list[dict]:
    if not vessel_ids:
        logger.warning("No vessel ids supplied -- nothing to extract")
        return []

    logger.info("Fetching events for %d vessel(s), %s to %s", len(vessel_ids), start_date, end_date)

    def fetch_page(offset, limit):
        return client.get_events(
            vessel_ids=vessel_ids,
            dataset=FISHING_EVENTS_DATASET,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    return client.paginate(fetch_page)


def lambda_handler(event=None, context=None):
    event = event or {}
    run_id = event.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    window = compute_extraction_window()
    if window is None:
        # Still write an empty batch rather than nothing at all -- validate.py
        # downstream unconditionally reads a raw/events file for this run_id,
        # and a missing file is a real error there, not "treat as zero
        # records". An empty file is what "genuinely nothing new" should
        # look like to the rest of the pipeline.
        location = write_raw_records("events", [], run_id)
        return {
            "run_id": run_id,
            "record_count": 0,
            "location": location,
            "skipped": True,
            "reason": "no new window to extract yet",
        }
    start_date, end_date = window

    client = GFWClient()
    vessel_ids = event.get("vessel_ids")
    if not vessel_ids:
        logger.info("No vessel_ids in event -- resolving them directly (standalone run)")
        vessel_ids = vessel_ids_from_records(extract_vessels(client))

    records = extract_events(client, vessel_ids, start_date, end_date)
    location = write_raw_records("events", records, run_id)

    # Only advance the watermark after a successful write -- if this run
    # fails partway through, the next run picks up from the same
    # unadvanced start_date rather than silently skipping a window.
    write_watermark(EVENTS_WATERMARK_KEY, end_date)

    return {
        "run_id": run_id,
        "record_count": len(records),
        "location": location,
    }


if __name__ == "__main__":
    print(lambda_handler())
