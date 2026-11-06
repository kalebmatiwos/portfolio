-- One row per self-reported identity snapshot (a vessel can carry more
-- than one internal id over its transmission history -- see GFW's "Why
-- am I seeing multiple ids when I search for a vessel?" doc). dim_vessel
-- collapses this to one row per vessel_id; this staging layer just
-- unnests and renames.
--
-- Assumes a Glue table over the clean/vessels S3 zone with
-- selfReportedInfo typed as array<struct<...>> -- adjust column casing
-- if your crawler produced different names (Glue/Hive lowercases by
-- default unless configured otherwise).

select
    self.id as vessel_id,
    self.ssvid as mmsi,
    self.shipname as ship_name,
    self.flag,
    self.callsign,
    self.imo,
    try_cast(self.transmissiondatefrom as timestamp) as transmission_date_from,
    try_cast(self.transmissiondateto as timestamp) as transmission_date_to
from {{ source('gfw_clean', 'dataset_vessels') }} as entry
cross join unnest(entry.selfreportedinfo) as t(self)
where self.id is not null
