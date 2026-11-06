"""
Unit tests for compute_extraction_window() in extract_events.py.
read_watermark is mocked throughout, so these test the date-window
logic in isolation from actual storage (S3 or local).
"""

from datetime import datetime, timezone
from unittest.mock import patch

from extract_events import compute_extraction_window


FIXED_NOW = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)


@patch("extract_events.read_watermark", return_value=None)
def test_first_run_with_no_watermark_looks_back_the_initial_window(mock_watermark):
    window = compute_extraction_window(now=FIXED_NOW)
    assert window is not None
    start, end = window
    # end = now - EVENTS_LAG_DAYS (5) = 2026-08-05
    assert end == "2026-08-05"
    # start = end - EVENTS_INITIAL_LOOKBACK_DAYS (30) = 2026-07-06
    assert start == "2026-07-06"


@patch("extract_events.read_watermark", return_value="2026-08-01")
def test_existing_watermark_is_used_as_start_date(mock_watermark):
    window = compute_extraction_window(now=FIXED_NOW)
    assert window == ("2026-08-01", "2026-08-05")


@patch("extract_events.read_watermark", return_value="2026-08-05")
def test_watermark_already_caught_up_returns_none(mock_watermark):
    # A second run shortly after a successful one: the lag-adjusted end
    # date hasn't moved, so start == end -- nothing new to fetch. This is
    # the case that structurally prevents the duplicate-event issue.
    window = compute_extraction_window(now=FIXED_NOW)
    assert window is None


@patch("extract_events.read_watermark", return_value="2026-08-06")
def test_watermark_past_end_date_returns_none(mock_watermark):
    # Defensive case: watermark somehow ahead of the computed end date.
    # Should not happen in normal operation, but must not produce an
    # inverted (start > end) window if it ever does.
    window = compute_extraction_window(now=FIXED_NOW)
    assert window is None


@patch("extract_events.read_watermark", return_value="2026-08-01")
def test_a_day_later_the_window_advances_by_one_day(mock_watermark):
    later = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
    window = compute_extraction_window(now=later)
    assert window == ("2026-08-01", "2026-08-06")
