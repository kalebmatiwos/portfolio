-- One row per fishing event. Flattens the nested position/vessel/fishing
-- structs from the source into typed columns. "end" is quoted below
-- because it's a reserved word in Trino/Athena SQL.
--
-- Assumes a Glue table over the clean/events S3 zone with position,
-- vessel and fishing typed as struct<...> -- adjust column casing if
-- your crawler produced different names.
--
-- vessel_public_authorizations and bounding_box are passed through as
-- semi-structured (array<struct<...>> / array<double>) rather than
-- flattened further: publicAuthorizations can hold more than one RFMO
-- per vessel, and bounding_box's four values aren't decomposed into
-- named min/max lon/lat fields since GFW's docs don't explicitly
-- confirm that ordering -- see schemas.py for the same caveat.

select
    id as event_id,
    type as event_type,
    try_cast(start as timestamp) as event_start,
    try_cast("end" as timestamp) as event_end,
    position.lat as latitude,
    position.lon as longitude,
    vessel.id as vessel_id,
    vessel.name as vessel_name,
    vessel.publicauthorizations as vessel_public_authorizations,
    fishing.totaldistancekm as fishing_total_distance_km,
    fishing.averagespeedknots as fishing_average_speed_knots,
    fishing.averagedurationhours as fishing_average_duration_hours,
    fishing.potentialrisk as fishing_potential_risk,
    fishing.vesselpublicauthorizationstatus as vessel_public_authorization_status,
    boundingbox as bounding_box
from {{ source('gfw_clean', 'dataset_events') }}
where id is not null
