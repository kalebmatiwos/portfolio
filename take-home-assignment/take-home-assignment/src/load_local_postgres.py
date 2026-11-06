"""
Loads the local 'clean' zone into Postgres so you can browse pipeline
output through Adminer without needing AWS -- a local demo convenience,
NOT the production target (that's S3 + Glue + Athena + dbt; see
infra/template.yaml and dbt/).

The transform logic here deliberately mirrors dbt/models/marts/ exactly
(same dedup-to-latest-snapshot rule for vessels, same fact grain for
events) so what you see in Adminer matches what the cloud path would
produce.

Usage:
    docker compose up -d
    python run_local_pipeline.py       # writes to data/clean/...
    python load_local_postgres.py       # loads that into Postgres
    # then open http://localhost:8080 (Adminer) -- System: PostgreSQL,
    # Server: db, Username: postgres, Password: postgres,
    # Database: take_home_assignment

Note: this mirrors fact_fishing_event's original column set. The
authorization/compliance fields and bounding_box added to the dbt marts
after inspecting a real sample (see README "Assumptions and scope")
haven't been carried into build_event_rows() or db/schema.sql yet.
"""

import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras

from storage import latest_run_id, read_records

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PG_DSN = os.environ.get("LOCAL_PG_DSN", "postgresql://postgres:postgres@localhost:5432/take_home_assignment")


def build_vessel_rows(clean_vessels: list[dict]) -> list[dict]:
    """Mirrors dim_vessel.sql: one row per vessel_id, keeping whichever
    self-reported snapshot has the most recent transmission_date_to.
    ISO 8601 strings sort correctly as plain strings, so this doesn't
    need to parse dates to compare them -- same trick the SQL's
    `ORDER BY transmission_date_to DESC` relies on implicitly.
    """
    latest_by_id: dict[str, dict] = {}
    for entry in clean_vessels:
        for self_reported in entry.get("selfReportedInfo", []):
            vessel_id = self_reported.get("id")
            if not vessel_id:
                continue
            current = latest_by_id.get(vessel_id)
            this_to = self_reported.get("transmissionDateTo") or ""
            current_to = (current or {}).get("transmissionDateTo") or ""
            if current is None or this_to > current_to:
                latest_by_id[vessel_id] = self_reported

    return [
        {
            "vessel_id": v["id"],
            "mmsi": v.get("ssvid"),
            "ship_name": v.get("shipname"),
            "flag": v.get("flag"),
            "callsign": v.get("callsign"),
            "imo": v.get("imo"),
            "transmission_date_from": v.get("transmissionDateFrom"),
            "transmission_date_to": v.get("transmissionDateTo"),
        }
        for v in latest_by_id.values()
    ]


def build_event_rows(clean_events: list[dict]) -> list[dict]:
    """Mirrors fact_fishing_event.sql -- already at event grain coming in."""
    rows = []
    for e in clean_events:
        fishing = e.get("fishing") or {}
        rows.append(
            {
                "event_id": e["id"],
                "event_type": e["type"],
                "event_start": e["start"],
                "event_end": e["end"],
                "latitude": e["position"]["lat"],
                "longitude": e["position"]["lon"],
                "vessel_id": e["vessel"]["id"],
                "fishing_total_distance_km": fishing.get("totalDistanceKm"),
                "fishing_average_speed_knots": fishing.get("averageSpeedKnots"),
                "fishing_average_duration_hours": fishing.get("averageDurationHours"),
                "fishing_potential_risk": fishing.get("potentialRisk"),
            }
        )
    return rows


def upsert(conn, table: str, rows: list[dict], key_column: str) -> int:
    """Idempotent load -- safe to re-run the loader against the same or
    a newer run_id without creating duplicates."""
    if not rows:
        return 0
    columns = list(rows[0].keys())
    values = [[row[c] for c in columns] for row in rows]
    update_cols = [c for c in columns if c != key_column]
    query = f"""
        INSERT INTO {table} ({", ".join(columns)})
        VALUES %s
        ON CONFLICT ({key_column}) DO UPDATE SET
        {", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)}
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, query, values)
    conn.commit()
    return len(rows)


def main(run_id: Optional[str] = None):
    run_id = run_id or latest_run_id("clean", "vessels")
    logger.info("Loading run_id=%s into Postgres", run_id)

    vessel_rows = build_vessel_rows(read_records("clean", "vessels", run_id))
    event_rows = build_event_rows(read_records("clean", "events", run_id))

    conn = psycopg2.connect(PG_DSN)
    try:
        n_vessels = upsert(conn, "dim_vessel", vessel_rows, "vessel_id")
        n_events = upsert(conn, "fact_fishing_event", event_rows, "event_id")
    finally:
        conn.close()

    logger.info("Loaded %d vessel(s) and %d event(s) into Postgres", n_vessels, n_events)
    return {"run_id": run_id, "vessels_loaded": n_vessels, "events_loaded": n_events}


if __name__ == "__main__":
    print(main())
