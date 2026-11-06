-- One row per fishing event. The foreign key to dim_vessel is enforced
-- by a dbt `relationships` test (see schema.yml) rather than a runtime
-- join here -- validate.py already guarantees every event's vessel_id
-- exists in the vessel dimension before either dataset reaches this
-- layer, so an inner join would only ever silently hide a bug rather
-- than catch one; the test surfaces it instead.
--
-- Deduplicated here on purpose, the same way dim_vessel dedupes vessel
-- snapshots: because EVENTS_START_DATE/EVENTS_END_DATE in config.py are
-- a fixed historical window rather than "since last run," every pipeline
-- execution re-extracts the same events. S3 partitions by ingestion
-- date, not by run, so two executions on the same calendar day land two
-- copies of the same 20 events in that day's partition, and Athena
-- reads a partition as every file under it. The row_number() below is
-- an arbitrary tiebreaker, not a "pick the freshest version" -- unlike
-- dim_vessel's snapshots, these duplicates are byte-identical
-- re-extractions of the same GFW event, not genuinely different
-- versions of it.

with ranked as (
    select
        *,
        row_number() over (
            partition by event_id
            order by event_start desc
        ) as rn
    from {{ ref('stg_fishing_events') }}
)

select
    event_id,
    event_type,
    event_start,
    event_end,
    date_diff('minute', event_start, event_end) as duration_minutes,
    latitude,
    longitude,
    bounding_box,
    vessel_id,
    vessel_public_authorizations,
    fishing_total_distance_km,
    fishing_average_speed_knots,
    fishing_average_duration_hours,
    fishing_potential_risk,
    vessel_public_authorization_status
from ranked
where rn = 1
