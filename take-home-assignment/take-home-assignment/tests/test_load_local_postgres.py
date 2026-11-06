"""
Tests for the pure transform functions in load_local_postgres.py.
No Postgres connection needed -- these only test build_vessel_rows /
build_event_rows, which is where the actual transform logic (and any
bug in it) lives; upsert() is a thin, well-known psycopg2 pattern not
worth mocking a whole DB connection to re-prove.
"""

from load_local_postgres import build_event_rows, build_vessel_rows

CLEAN_VESSEL_ENTRY = {
    "dataset": "public-global-vessel-identity:v20231026",
    "selfReportedInfo": [
        {
            "id": "9b3e9019d-d67f-005a-9593-b66b997559e5",
            "ssvid": "701000948",
            "shipname": "CLAUDINA",
            "flag": "ARG",
            "transmissionDateFrom": "2016-12-20T20:27:39Z",
            "transmissionDateTo": "2023-04-13T18:19:16Z",
        },
        {
            "id": "e9efd1586-61cf-74a8-757d-e8b4c0664c20",
            "ssvid": "701000948",
            "shipname": "CLAUDINA",
            "flag": "ARG",
            "transmissionDateFrom": "2012-01-01T04:38:08Z",
            "transmissionDateTo": "2016-09-15T15:07:46Z",
        },
    ],
}

CLEAN_EVENT = {
    "id": "49c5ab5a5ba4139b15ca9c039b0ea4f7",
    "type": "fishing",
    "start": "2017-02-28T23:09:29.000Z",
    "end": "2017-03-01T04:25:22.000Z",
    "position": {"lat": -47.1439, "lon": -62.7624},
    "vessel": {"id": "9b3e9019d-d67f-005a-9593-b66b997559e5", "name": "CLAUDINA"},
    "fishing": {"totalDistanceKm": 3.93, "potentialRisk": False},
}


def test_build_vessel_rows_one_row_per_id():
    rows = build_vessel_rows([CLEAN_VESSEL_ENTRY])
    assert len(rows) == 2
    ids = {r["vessel_id"] for r in rows}
    assert ids == {"9b3e9019d-d67f-005a-9593-b66b997559e5", "e9efd1586-61cf-74a8-757d-e8b4c0664c20"}


def test_build_vessel_rows_keeps_most_recent_snapshot_per_id():
    older = {"selfReportedInfo": [{**CLEAN_VESSEL_ENTRY["selfReportedInfo"][0], "shipname": "OLD_NAME",
                                    "transmissionDateTo": "2020-01-01T00:00:00Z"}]}
    newer = {"selfReportedInfo": [{**CLEAN_VESSEL_ENTRY["selfReportedInfo"][0], "shipname": "NEW_NAME",
                                    "transmissionDateTo": "2023-04-13T18:19:16Z"}]}

    rows = build_vessel_rows([older, newer])
    assert len(rows) == 1
    assert rows[0]["ship_name"] == "NEW_NAME"


def test_build_vessel_rows_fields_mapped_correctly():
    rows = build_vessel_rows([CLEAN_VESSEL_ENTRY])
    row = next(r for r in rows if r["vessel_id"] == "9b3e9019d-d67f-005a-9593-b66b997559e5")
    assert row["mmsi"] == "701000948"
    assert row["ship_name"] == "CLAUDINA"
    assert row["flag"] == "ARG"


def test_build_event_rows_flattens_nested_fields():
    rows = build_event_rows([CLEAN_EVENT])
    assert len(rows) == 1
    row = rows[0]
    assert row["event_id"] == "49c5ab5a5ba4139b15ca9c039b0ea4f7"
    assert row["latitude"] == -47.1439
    assert row["longitude"] == -62.7624
    assert row["vessel_id"] == "9b3e9019d-d67f-005a-9593-b66b997559e5"
    assert row["fishing_total_distance_km"] == 3.93
    assert row["fishing_potential_risk"] is False


def test_build_event_rows_handles_missing_fishing_block():
    event = {**CLEAN_EVENT, "fishing": None}
    rows = build_event_rows([event])
    assert rows[0]["fishing_total_distance_km"] is None
