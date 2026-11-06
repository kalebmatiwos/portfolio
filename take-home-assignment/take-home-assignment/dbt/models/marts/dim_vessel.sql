-- One row per vessel_id. A vessel can appear more than once in
-- stg_vessels (multiple internal ids, or the same id seen across
-- multiple runs once this is scheduled) -- this keeps the most
-- recently-transmitting snapshot per id.

with ranked as (
    select
        *,
        row_number() over (
            partition by vessel_id
            order by transmission_date_to desc nulls last
        ) as rn
    from {{ ref('stg_vessels') }}
)

select
    vessel_id,
    mmsi,
    ship_name,
    flag,
    callsign,
    imo,
    transmission_date_from,
    transmission_date_to
from ranked
where rn = 1
