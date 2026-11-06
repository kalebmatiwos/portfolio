"""
Landing-zone storage helper.

Writes/reads newline-delimited JSON, partitioned by zone, dataset and
ingestion date -- e.g.:

    raw/gfw/dataset=vessels/date=2026-07-25/run-20260725T101500Z.jsonl
    clean/gfw/dataset=events/date=2026-07-25/run-20260725T101500Z.jsonl
    quarantine/gfw/dataset=events/date=2026-07-25/run-20260725T101500Z.jsonl

Zones:
    raw         -- exactly what the API returned, untouched
    clean       -- records that passed validate.py's checks
    quarantine  -- records that failed, alongside the reason they failed

Falls back to writing/reading under a local directory when RAW_BUCKET
isn't set, so the whole pipeline is runnable end-to-end on a laptop
with no AWS credentials.
"""

import glob
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from config import LOCAL_DATA_DIR, S3_BUCKET

logger = logging.getLogger(__name__)


def _partition_key(zone: str, dataset: str, run_id: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{zone}/gfw/dataset={dataset}/date={date_str}/run-{run_id}.jsonl"


def write_records(zone: str, dataset: str, records: list[dict], run_id: str) -> str:
    """Write a batch of records as newline-delimited JSON to the given zone.

    Returns the key/path written to. Uses S3 when S3_BUCKET is set,
    otherwise writes under LOCAL_DATA_DIR for local development.
    """
    key = _partition_key(zone, dataset, run_id)
    body = io.StringIO()
    for record in records:
        body.write(json.dumps(record, default=str))
        body.write("\n")
    payload = body.getvalue()

    if S3_BUCKET:
        return _write_s3(key, payload)
    return _write_local(key, payload)


def write_raw_records(dataset: str, records: list[dict], run_id: str) -> str:
    """Back-compat convenience wrapper -- writes to the 'raw' zone."""
    return write_records("raw", dataset, records, run_id)


def read_records(zone: str, dataset: str, run_id: str) -> list[dict]:
    """Read back a batch previously written by write_records for the same run_id."""
    key = _partition_key(zone, dataset, run_id)
    if S3_BUCKET:
        payload = _read_s3(key)
    else:
        payload = _read_local(key)
    return [json.loads(line) for line in payload.splitlines() if line.strip()]


def _write_s3(key: str, payload: str) -> str:
    import boto3  # imported lazily so local dev doesn't need boto3 installed

    s3 = boto3.client("s3")
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=payload.encode("utf-8"))
    location = f"s3://{S3_BUCKET}/{key}"
    logger.info("Wrote %d bytes to %s", len(payload), location)
    return location


def _write_local(key: str, payload: str) -> str:
    # key is always forward-slash-separated (S3-style), so split it before
    # joining rather than passing it as one string -- os.path.join only
    # native-izes the join point between its own arguments, not slashes
    # already embedded inside one of them. Passing it unsplit produced
    # paths like "data\raw/gfw/..." on Windows -- functional (Windows
    # tolerates mixed separators) but not clean.
    path = os.path.join(LOCAL_DATA_DIR, *key.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(payload)
    logger.info("Wrote %d bytes to %s", len(payload), path)
    return path


def _read_s3(key: str) -> str:
    import boto3

    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return obj["Body"].read().decode("utf-8")


def _read_local(key: str) -> str:
    path = os.path.join(LOCAL_DATA_DIR, *key.split("/"))
    with open(path) as f:
        return f.read()


def latest_run_id(zone: str, dataset: str) -> str:
    """Convenience for local dev / tests: find the most recent run_id written
    for a given zone+dataset, by scanning LOCAL_DATA_DIR. S3 equivalent would
    list objects under the prefix instead -- not needed for this take-home."""
    pattern = os.path.join(LOCAL_DATA_DIR, zone, "gfw", f"dataset={dataset}", "date=*", "run-*.jsonl")
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No {zone}/{dataset} runs found under {LOCAL_DATA_DIR}")
    latest = matches[-1]
    return os.path.basename(latest).removeprefix("run-").removesuffix(".jsonl")


def read_watermark(key: str) -> Optional[str]:
    """Read a small piece of persisted state (currently just the events
    extraction watermark -- see extract_events.py). Returns None if it
    doesn't exist yet, rather than raising: this is the one place in this
    module where a missing key is an expected, normal condition (the
    very first run ever, before any watermark has been written), not an
    error to propagate.
    """
    if S3_BUCKET:
        import boto3

        s3 = boto3.client("s3")
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            return obj["Body"].read().decode("utf-8").strip()
        except s3.exceptions.NoSuchKey:
            return None
    else:
        path = os.path.join(LOCAL_DATA_DIR, *key.split("/"))
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read().strip()


def write_watermark(key: str, value: str) -> str:
    """Persist a small piece of state (plain text, not JSONL -- unlike
    write_records, this isn't a batch of newline-delimited records)."""
    if S3_BUCKET:
        return _write_s3(key, value)
    return _write_local(key, value)
