"""
Unit tests for validate.py. No network, no AWS -- pure logic against
inline fixtures shaped like real GFW responses (the vessel fixture
trimmed from GFW's own quick-start docs; the event fixture trimmed from
an actual sample record pulled from the deployed pipeline's raw zone).

Run with: pytest tests/test_validate.py
(from the project root, with src/ on PYTHONPATH -- see conftest.py)
"""

from validate import validate_events, validate_vessels

GOOD_VESSEL = {
    "dataset": "public-global-vessel-identity:v20231026",
    "selfReportedInfo": [
        {
            "id": "9b3e9019d-d67f-005a-9593-b66b997559e5",
            "ssvid": "701000948",
            "shipname": "CLAUDINA",
            "flag": "ARG",
            "transmissionDateFrom": "2016-12-20T20:27:39Z",
            "transmissionDateTo": "2023-04-13T18:19:16Z",
        }
    ],
}

GOOD_EVENT = {
    "id": "49c5ab5a5ba4139b15ca9c039b0ea4f7",
    "type": "fishing",
    "start": "2017-02-28T23:09:29.000Z",
    "end": "2017-03-01T04:25:22.000Z",
    "position": {"lat": -47.1439, "lon": -62.7624},
    "regions": {"eez": ["8466"]},
    "boundingBox": [-62.752836666700006, -47.16, -62.768585, -47.1277183333],
    "vessel": {
        "id": "9b3e9019d-d67f-005a-9593-b66b997559e5",
        "name": "CLAUDINA",
        "publicAuthorizations": [
            # hasPubliclyListedAuthorization really is the string "false"
            # in GFW's response, not a JSON boolean -- kept exactly as
            # observed rather than "cleaned up" to what looks more correct.
            {"rfmo": "CCSBT", "hasPubliclyListedAuthorization": "false"},
            {"rfmo": "ICCAT", "hasPubliclyListedAuthorization": "false"},
        ],
    },
    "fishing": {
        "totalDistanceKm": 3.93,
        "potentialRisk": False,
        "vesselPublicAuthorizationStatus": "not_matching_relevant_public_authorization",
    },
}


# --- vessels -----------------------------------------------------------------


def test_valid_vessel_passes():
    clean, quarantined = validate_vessels([GOOD_VESSEL])
    assert len(clean) == 1
    assert len(quarantined) == 0


def test_vessel_missing_self_reported_info_is_quarantined():
    bad = {**GOOD_VESSEL, "selfReportedInfo": []}
    clean, quarantined = validate_vessels([bad])
    assert len(clean) == 0
    assert quarantined[0]["reason_code"] == "no_vessel_id"


def test_vessel_missing_required_field_fails_schema():
    bad = {"selfReportedInfo": [{"ssvid": "701000948"}]}  # no "id"
    clean, quarantined = validate_vessels([bad])
    assert len(clean) == 0
    assert quarantined[0]["reason_code"] == "schema_invalid"


def test_duplicate_vessel_id_in_same_batch_is_quarantined():
    clean, quarantined = validate_vessels([GOOD_VESSEL, GOOD_VESSEL])
    assert len(clean) == 1
    assert len(quarantined) == 1
    assert quarantined[0]["reason_code"] == "duplicate_vessel_id"


# --- events --------------------------------------------------------------------


def test_valid_event_passes():
    clean, quarantined = validate_events([GOOD_EVENT])
    assert len(clean) == 1
    assert len(quarantined) == 0


def test_event_authorization_and_bounding_box_fields_survive_into_clean_output():
    # Regression coverage for fields added after inspecting a real sample --
    # extra="ignore" on the Pydantic models means a field silently
    # disappearing on a future schema tweak wouldn't raise anywhere else.
    clean, quarantined = validate_events([GOOD_EVENT])
    assert len(quarantined) == 0
    record = clean[0]
    assert record["boundingBox"] == GOOD_EVENT["boundingBox"]
    assert record["fishing"]["vesselPublicAuthorizationStatus"] == "not_matching_relevant_public_authorization"
    auths = record["vessel"]["publicAuthorizations"]
    assert len(auths) == 2
    assert auths[0]["rfmo"] == "CCSBT"
    assert auths[0]["hasPubliclyListedAuthorization"] == "false"  # string, not bool -- see fixture comment


def test_event_end_before_start_is_quarantined():
    bad = {**GOOD_EVENT, "id": "bad-1", "start": "2017-03-05T00:00:00Z", "end": "2017-03-01T00:00:00Z"}
    clean, quarantined = validate_events([bad])
    assert len(clean) == 0
    assert quarantined[0]["reason_code"] == "invalid_date_range"


def test_event_position_out_of_range_is_quarantined():
    bad = {**GOOD_EVENT, "id": "bad-2", "position": {"lat": 200.0, "lon": 20.0}}
    clean, quarantined = validate_events([bad])
    assert len(clean) == 0
    assert quarantined[0]["reason_code"] == "position_out_of_range"


def test_duplicate_event_id_is_quarantined():
    clean, quarantined = validate_events([GOOD_EVENT, GOOD_EVENT])
    assert len(clean) == 1
    assert quarantined[0]["reason_code"] == "duplicate_event_id"


def test_unknown_vessel_id_is_quarantined_when_known_ids_supplied():
    clean, quarantined = validate_events([GOOD_EVENT], known_vessel_ids={"some-other-vessel-id"})
    assert len(clean) == 0
    assert quarantined[0]["reason_code"] == "unknown_vessel_id"


def test_known_vessel_id_passes_referential_check():
    clean, quarantined = validate_events(
        [GOOD_EVENT], known_vessel_ids={"9b3e9019d-d67f-005a-9593-b66b997559e5"}
    )
    assert len(clean) == 1
    assert len(quarantined) == 0
