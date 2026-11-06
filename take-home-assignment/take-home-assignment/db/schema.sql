-- Mirrors the shape of dbt/models/marts/dim_vessel.sql and
-- fact_fishing_event.sql, so querying this local Postgres instance
-- shows the same structure the cloud/Athena target produces.
--
-- This is a LOCAL DEMO CONVENIENCE ONLY, for visually inspecting
-- pipeline output on your own machine via Adminer. The actual cloud
-- target is S3 + Glue + Athena + dbt (see infra/template.yaml and
-- dbt/) -- that's what the take-home's "design for cloud deployment"
-- requirement refers to, not this.
--
-- Auto-run by the official postgres image on first container start
-- (mounted into /docker-entrypoint-initdb.d/ by docker-compose.yml).

CREATE TABLE IF NOT EXISTS dim_vessel (
    vessel_id               TEXT PRIMARY KEY,
    mmsi                     TEXT,
    ship_name                TEXT,
    flag                      TEXT,
    callsign                  TEXT,
    imo                       TEXT,
    transmission_date_from   TIMESTAMPTZ,
    transmission_date_to     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS fact_fishing_event (
    event_id                        TEXT PRIMARY KEY,
    event_type                      TEXT,
    event_start                     TIMESTAMPTZ,
    event_end                       TIMESTAMPTZ,
    latitude                        DOUBLE PRECISION,
    longitude                       DOUBLE PRECISION,
    vessel_id                       TEXT REFERENCES dim_vessel(vessel_id),
    fishing_total_distance_km       DOUBLE PRECISION,
    fishing_average_speed_knots     DOUBLE PRECISION,
    fishing_average_duration_hours  DOUBLE PRECISION,
    fishing_potential_risk          BOOLEAN
);
