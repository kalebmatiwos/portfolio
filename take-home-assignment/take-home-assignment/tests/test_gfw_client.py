"""
Unit tests for gfw_client.py. The HTTP layer (requests.Session.request)
is mocked throughout -- these test the retry/backoff and pagination
logic in isolation, not the real GFW API (globalfishingwatch.org isn't
reachable from this sandbox, and shouldn't be needed to trust this logic
anyway). time.sleep is patched out so retry tests run instantly.

Run with: pytest tests/test_gfw_client.py
"""

from unittest.mock import MagicMock, patch

import pytest

from gfw_client import GFWAPIError, GFWClient


def make_client():
    return GFWClient(token="dummy", max_retries=3, timeout=5)


def mock_response(status_code, json_body=None, headers=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    resp.headers = headers or {}
    resp.text = text
    return resp


@patch("time.sleep", return_value=None)
def test_200_returns_json_immediately(mock_sleep):
    client = make_client()
    client.session.request = MagicMock(return_value=mock_response(200, {"ok": True}))

    result = client._request("GET", "/v3/events")

    assert result == {"ok": True}
    assert client.session.request.call_count == 1
    mock_sleep.assert_not_called()


@patch("time.sleep", return_value=None)
def test_429_retries_then_succeeds(mock_sleep):
    client = make_client()
    client.session.request = MagicMock(
        side_effect=[
            mock_response(429, headers={"Retry-After": "1"}),
            mock_response(200, {"ok": True}),
        ]
    )

    result = client._request("GET", "/v3/events")

    assert result == {"ok": True}
    assert client.session.request.call_count == 2
    mock_sleep.assert_called_once()


@patch("time.sleep", return_value=None)
def test_exhausting_retries_raises(mock_sleep):
    client = make_client()  # max_retries=3
    client.session.request = MagicMock(return_value=mock_response(503))

    with pytest.raises(GFWAPIError):
        client._request("GET", "/v3/events")

    # attempts 1..4 (initial + max_retries), then raise
    assert client.session.request.call_count == 4


@patch("time.sleep", return_value=None)
def test_non_retried_4xx_raises_immediately(mock_sleep):
    client = make_client()
    client.session.request = MagicMock(return_value=mock_response(404, text="not found"))

    with pytest.raises(GFWAPIError):
        client._request("GET", "/v3/events")

    assert client.session.request.call_count == 1  # no retries burned on a 404
    mock_sleep.assert_not_called()


def test_backoff_is_capped():
    assert GFWClient._backoff(1) == 2
    assert GFWClient._backoff(2) == 4
    assert GFWClient._backoff(10) == 30  # capped, not 2**10


@patch("time.sleep", return_value=None)
def test_search_vessels_never_sends_offset(mock_sleep):
    # Regression test: /v3/vessels/search's schema doesn't define an
    # offset property at all, and passing one returns a live 422
    # ("property offset should not exist") -- confirmed against the
    # real API. Unlike /v3/events, which does accept offset.
    client = make_client()
    client.session.request = MagicMock(return_value=mock_response(200, {"entries": [], "total": 0}))

    client.search_vessels(query="7831410", dataset="public-global-vessel-identity:latest")

    sent_params = client.session.request.call_args.kwargs["params"]
    assert "offset" not in sent_params


# --- pagination ------------------------------------------------------------------


def test_paginate_single_page():
    client = make_client()
    page = {"entries": [{"id": 1}, {"id": 2}], "total": 2, "nextOffset": None}
    fetched = client.paginate(lambda offset, limit: page)
    assert fetched == [{"id": 1}, {"id": 2}]


def test_paginate_multiple_pages():
    client = make_client()
    pages = [
        {"entries": [{"id": 1}], "total": 3, "nextOffset": 1},
        {"entries": [{"id": 2}], "total": 3, "nextOffset": 2},
        {"entries": [{"id": 3}], "total": 3, "nextOffset": None},
    ]
    calls = {"n": 0}

    def fetch_page(offset, limit):
        page = pages[calls["n"]]
        calls["n"] += 1
        return page

    fetched = client.paginate(fetch_page)
    assert fetched == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert calls["n"] == 3


def test_paginate_stops_on_empty_page():
    client = make_client()
    fetched = client.paginate(lambda offset, limit: {"entries": [], "total": 0, "nextOffset": None})
    assert fetched == []
