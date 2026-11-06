"""
Configuration for the Take Home Assignment pipeline.

Auth: the GFW API token is NEVER hardcoded. It's read from the
GFW_API_TOKEN environment variable. In AWS, that variable is set
directly by Lambda from Secrets Manager at deploy time -- no .env file
exists there, and none is needed.

Locally, python-dotenv (see requirements-dev.txt) is an optional
convenience for loading .env -- optional and guarded below so this
file works identically whether it's installed or not. It's
deliberately NOT in src/requirements.txt: that file is what `sam
build` packages into the Lambda deployment zip, and Lambda has no use
for it -- keeping it out keeps that package lean and keeps this class
of "works locally, ImportModuleError in Lambda" bug from coming back.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Not installed -- either you're in Lambda (expected, fine, GFW_API_TOKEN
    # is already set for you) or you're running locally without it (also
    # fine, just export the variable yourself instead of using a .env file).
    pass

# --- Auth -------------------------------------------------------------
GFW_API_TOKEN = os.environ["GFW_API_TOKEN"]

# --- API ----------------------------------------------------------------
GFW_BASE_URL = "https://gateway.api.globalfishingwatch.org"
VESSEL_IDENTITY_DATASET = "public-global-vessel-identity:latest"
FISHING_EVENTS_DATASET = "public-global-fishing-events:latest"

# --- Demo scope -----------------------------------------------------------
# Deliberately bounded for a 4-hour take-home: a small, fixed set of
# vessel search queries (IMO numbers) rather than a full vessel-discovery
# service. Each query is resolved to an internal vessel id by the Vessels
# API search endpoint in extract_vessels.py, and that id is what
# extract_events.py then uses to pull fishing events.
#
# Swap or extend this list with any IMO/MMSI/vessel name you want to
# demo with -- "7831410" is the example vessel (CLAUDINA) used in GFW's
# own quick-start docs, kept here as a known-good default.
#
# See README "Scaling" section for how this generalizes to a proper
# discovery mechanism (e.g. a 4Wings report grouped by vessel_id for a
# region) instead of a fixed seed list.
SEED_VESSEL_QUERIES = [
    "7831410",
]

# Incremental, not a fixed historical window: each run extracts events
# from where the last successful run left off, up to today minus a
# publication-lag buffer, rather than re-processing a static range every
# time. See extract_events.py's compute_extraction_window() for the
# actual logic, and the README's "Troubleshooting" section for the
# duplicate-event issue this replaces a fixed window to avoid recreating.

# GFW's own docs state SAR vessel detections lag by up to 5 days before
# being available; the AIS-based datasets this pipeline actually reads
# are documented closer to 3-4 days near-real-time. 5 is used here as a
# deliberately conservative buffer regardless -- querying past what's
# genuinely published yet just returns fewer/no results, while querying
# too close to "now" risks pulling an incomplete picture of a day GFW
# hasn't finished processing.
EVENTS_LAG_DAYS = 5

# Only used the very first time this ever runs, before any watermark
# exists yet -- how far back to look on that first run.
EVENTS_INITIAL_LOOKBACK_DAYS = 30

# Where the watermark (the end date of the last successful extraction)
# is persisted -- same bucket/local-dir every other zone uses, under a
# "state/" prefix rather than "raw/clean/quarantine" since it isn't a
# batch of records.
EVENTS_WATERMARK_KEY = "state/events_watermark.txt"

# --- Storage --------------------------------------------------------------
# Falls back to a local directory when RAW_BUCKET isn't set, so the
# extractors are runnable without any AWS credentials during development.
# storage.py appends <zone>/gfw/dataset=.../date=.../run-....jsonl under
# this, so LOCAL_DATA_DIR should NOT itself contain "raw" -- that's a
# zone name, added per-call.
S3_BUCKET = os.environ.get("RAW_BUCKET")
LOCAL_DATA_DIR = "data"
