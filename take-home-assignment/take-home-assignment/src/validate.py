"""
Validation and quality-check layer.

Reads raw JSONL previously landed by extract_vessels.py / extract_events.py,
validates each record against schemas.py, runs a handful of business-level
quality checks on top of schema validation, and routes the results to the
'clean' zone (passed) or 'quarantine' zone (failed, tagged with a reason)
via storage.py.

Runnable standalone for local development, and importable as a Lambda
handler for the validation step in the Step Functions pipeline.
"""

import logging
from typing import Optional

from pydantic import ValidationError

from schemas import EventEntry, VesselSearchEntry
from storage import latest_run_id, read_records, write_records

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _reject(code: str, detail: str, raw: dict) -> dict:
    return {"reason_code": code, "reason_detail": detail, "raw": raw}


def validate_vessels(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Validate vessel search entries. Returns (clean, quarantined)."""
    clean: list[dict] = []
    quarantined: list[dict] = []
    seen_ids: set[str] = set()

    for raw in raw_records:
        try:
            entry = VesselSearchEntry.model_validate(raw)
        except ValidationError as exc:
            quarantined.append(_reject("schema_invalid", exc.errors()[0]["msg"], raw))
            continue

        ids = [info.id for info in entry.selfReportedInfo if info.id]
        if not ids:
            quarantined.append(_reject("no_vessel_id", "no usable vessel id in selfReportedInfo", raw))
            continue

        new_ids = [i for i in ids if i not in seen_ids]
        if not new_ids:
            quarantined.append(_reject("duplicate_vessel_id", "already seen this run", raw))
            continue

        seen_ids.update(new_ids)
        clean.append(entry.model_dump(mode="json"))

    return clean, quarantined


def validate_events(
    raw_records: list[dict], known_vessel_ids: Optional[set[str]] = None
) -> tuple[list[dict], list[dict]]:
    """Validate fishing event entries. Returns (clean, quarantined).

    known_vessel_ids, when provided, adds a referential-integrity check:
    an event referencing a vessel id we never extracted an identity
    record for is quarantined rather than kept -- it would otherwise
    become an orphaned fact row with nothing to join to in dim_vessel.
    """
    clean: list[dict] = []
    quarantined: list[dict] = []
    seen_ids: set[str] = set()

    for raw in raw_records:
        try:
            event = EventEntry.model_validate(raw)
        except ValidationError as exc:
            quarantined.append(_reject("schema_invalid", exc.errors()[0]["msg"], raw))
            continue

        if event.id in seen_ids:
            quarantined.append(_reject("duplicate_event_id", "already seen this run", raw))
            continue

        if event.end < event.start:
            quarantined.append(_reject("invalid_date_range", f"end {event.end} before start {event.start}", raw))
            continue

        if not (-90 <= event.position.lat <= 90) or not (-180 <= event.position.lon <= 180):
            quarantined.append(_reject("position_out_of_range", str(event.position), raw))
            continue

        if known_vessel_ids is not None and event.vessel.id not in known_vessel_ids:
            quarantined.append(_reject("unknown_vessel_id", event.vessel.id, raw))
            continue

        seen_ids.add(event.id)
        clean.append(event.model_dump(mode="json"))

    return clean, quarantined


def _log_summary(dataset: str, clean: list[dict], quarantined: list[dict]) -> None:
    total = len(clean) + len(quarantined)
    logger.info("%s: %d/%d passed (%d quarantined)", dataset, len(clean), total, len(quarantined))
    reasons: dict[str, int] = {}
    for q in quarantined:
        reasons[q["reason_code"]] = reasons.get(q["reason_code"], 0) + 1
    for reason, count in sorted(reasons.items()):
        logger.info("  - %d quarantined for: %s", count, reason)


def lambda_handler(event=None, context=None):
    event = event or {}
    run_id = event.get("run_id") or latest_run_id("raw", "vessels")

    raw_vessels = read_records("raw", "vessels", run_id)
    clean_vessels, quarantined_vessels = validate_vessels(raw_vessels)
    _log_summary("vessels", clean_vessels, quarantined_vessels)
    write_records("clean", "vessels", clean_vessels, run_id)
    write_records("quarantine", "vessels", quarantined_vessels, run_id)

    known_vessel_ids = {info["id"] for v in clean_vessels for info in v["selfReportedInfo"]}

    raw_events = read_records("raw", "events", run_id)
    clean_events, quarantined_events = validate_events(raw_events, known_vessel_ids)
    _log_summary("events", clean_events, quarantined_events)
    write_records("clean", "events", clean_events, run_id)
    write_records("quarantine", "events", quarantined_events, run_id)

    return {
        "run_id": run_id,
        "vessels": {"clean": len(clean_vessels), "quarantined": len(quarantined_vessels)},
        "events": {"clean": len(clean_events), "quarantined": len(quarantined_events)},
    }


if __name__ == "__main__":
    print(lambda_handler())
