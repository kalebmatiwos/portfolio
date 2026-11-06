"""
Local end-to-end runner: extract vessels -> extract events -> validate,
threading the same run_id and vessel_ids through each step exactly the
way the Step Functions state machine in infra/template.yaml does (each
step's output becomes the next step's input event).

    python run_local_pipeline.py

Useful for demoing the whole pipeline without deploying anything --
writes to data/raw/, data/clean/ and data/quarantine/ locally when
RAW_BUCKET isn't set.
"""

import json
import logging

import extract_events
import extract_vessels
import validate

logging.basicConfig(level=logging.INFO)


def main():
    vessels_result = extract_vessels.lambda_handler()
    events_result = extract_events.lambda_handler(vessels_result)
    validate_result = validate.lambda_handler(events_result)

    print(json.dumps(
        {"vessels": vessels_result, "events": events_result, "validate": validate_result},
        indent=2,
        default=str,
    ))


if __name__ == "__main__":
    main()
