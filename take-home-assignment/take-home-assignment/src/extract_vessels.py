"""
Extract vessel identity records from the GFW Vessels API search
endpoint, for the seed queries configured in config.py, and land them
as raw JSON.

Runnable directly for local development, and importable as a Lambda
handler (`lambda_handler`) for scheduled deployment.
"""

import logging
from datetime import datetime, timezone

from config import SEED_VESSEL_QUERIES, VESSEL_IDENTITY_DATASET
from gfw_client import GFWClient
from storage import write_raw_records

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_vessels(client: GFWClient) -> list[dict]:
    """Resolve each seed query in config.py to vessel search records.

    One call per query, not paginated -- see search_vessels()'s
    docstring for why. If a query genuinely matches more vessels than
    fit in one page, that's logged loudly rather than silently dropped.
    """
    all_records: list[dict] = []
    for query in SEED_VESSEL_QUERIES:
        logger.info("Searching vessels for query=%s", query)

        response = client.search_vessels(query=query, dataset=VESSEL_IDENTITY_DATASET, limit=50)
        entries = response.get("entries", [])
        total = response.get("total", len(entries))

        if total > len(entries):
            logger.warning(
                "query=%s matched %d vessels but only %d came back in one page -- "
                "raise the limit in search_vessels() if you need all of them",
                query, total, len(entries),
            )

        logger.info("Found %d vessel record(s) for query=%s", len(entries), query)
        all_records.extend(entries)
    return all_records


def vessel_ids_from_records(records: list[dict]) -> list[str]:
    """Pull the internal vessel ids the Events API expects out of search results.

    A vessel can carry more than one internal id across its transmission
    history (see selfReportedInfo in the GFW docs), so this collects all
    of them rather than assuming just one per vessel.
    """
    ids: set[str] = set()
    for record in records:
        for entry in record.get("selfReportedInfo", []):
            if entry.get("id"):
                ids.add(entry["id"])
    return sorted(ids)


def lambda_handler(event=None, context=None):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    client = GFWClient()

    records = extract_vessels(client)
    location = write_raw_records("vessels", records, run_id)

    vessel_ids = vessel_ids_from_records(records)
    logger.info("Resolved %d vessel id(s): %s", len(vessel_ids), vessel_ids)

    return {
        "run_id": run_id,
        "record_count": len(records),
        "location": location,
        "vessel_ids": vessel_ids,
    }


if __name__ == "__main__":
    print(lambda_handler())
