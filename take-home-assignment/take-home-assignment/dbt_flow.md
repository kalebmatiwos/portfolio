# dbt Setup and Run — Take Home Assignment

A record of how I got dbt running against the deployed pipeline's Athena
and Glue Data Catalog, from a clean install through to a fully passing
`dbt run` and `dbt test`. Written as a reference in case I need to set
this up again on a fresh machine, or hand it to someone else doing the
same.

## 1. Installing dbt

I installed the Athena adapter, which pulls in a matching dbt-core
version automatically:

```bash
pip install dbt-athena-community
```

## 2. Installing package dependencies

The project's `schema.yml` uses `dbt_utils.accepted_range` for the
latitude/longitude tests, so the `dbt_utils` package needs to be
installed before anything else runs:

```
$ dbt deps
Running with dbt=1.12.0
Installing dbt-labs/dbt_utils
Installed from version 1.4.1
Up to date!
```

## 3. First connection check

I created `~/.dbt/profiles.yml` with an initial profile pointing at the
Athena workgroup and the Glue database I could see in the Athena query
editor at the time, then ran:

```
$ dbt debug
...
Connection:
  database: glue-crawler-database
  region_name: eu-west-2
  s3_staging_dir: s3://athena-take-home-assignment/results/
  schema: glue-crawler-database
  work_group: primary
Registered adapter: athena=1.11.0
  Connection test: [OK connection ok]

All checks passed!
```

This passed, which turned out to be a bit misleading — the connection
test only confirms Athena itself is reachable, not that the specific
database or tables it's pointed at actually exist.

## 4. First `dbt run` — wrong catalog

```
$ dbt run
...
[ERROR]: Encountered an error:
An error occurred (InvalidRequestException) when calling the
GetDataCatalog operation: DataCatalog glue-crawler-database was not found.
```

The root cause: in Athena, "Data Catalog" and "database" are two
different things, and dbt-athena's `database` field in `profiles.yml`
means the Data Catalog, not the Glue database. Every AWS account has
exactly one Data Catalog, always named `AwsDataCatalog` — that's a fixed
value, not something that varies per account. I'd put my Glue database
name in the wrong field.

**Fix:** set `database: AwsDataCatalog` in `profiles.yml`, leaving the
Glue database name in `schema` where it belonged.

## 5. Second `dbt run` — wrong database

With the catalog fixed, the run got further but still failed:

```
$ dbt run
...
1 of 4 ERROR creating sql view model glue-crawler-database.stg_fishing_events
  Runtime Error
    line 26:6: Table 'awsdatacatalog.glue-crawler-database.dataset_events' does not exist
2 of 4 ERROR creating sql view model glue-crawler-database.stg_vessels
  Runtime Error
    line 25:6: Table 'awsdatacatalog.glue-crawler-database.dataset_vessels' does not exist
```

This one took checking the Glue console directly to resolve. It turned
out `glue-crawler-database` was a separate database created by a crawler
I'd run manually while testing earlier — not the one the deployed
CloudFormation stack actually populates. The real database, confirmed in
Glue under Catalogues → Databases, was `gfw_clean`, containing exactly
the two tables expected: `dataset_vessels` and `dataset_events`.

**Fix:** updated `schema` in `profiles.yml`, and the `schema` value in
`dbt/models/staging/sources.yml`, from `glue-crawler-database` to
`gfw_clean`. Table names in `sources.yml` (`dataset_vessels`,
`dataset_events`) were already correct.

Final working `profiles.yml`:

```yaml
take_home_assignment:
  target: dev
  outputs:
    dev:
      type: athena
      s3_staging_dir: s3://athena-take-home-assignment/results/
      region_name: eu-west-2
      database: AwsDataCatalog
      schema: gfw_clean
      work_group: primary
```

## 6. A deprecation warning, fixed along the way

The same run also surfaced this:

```
[WARNING][MissingArgumentsPropertyInGenericTestDeprecation]: Deprecated
functionality
Found top-level arguments to test `relationships` defined on
'fact_fishing_event' in package 'take_home_assignment' (models\schema.yml).
Arguments to generic tests should be nested under the `arguments` property.
```

dbt 1.12 changed how generic test arguments are declared — `to`/`field`/
`values`/`min_value`/`max_value` need to sit under a nested `arguments:`
key now, rather than directly under the test name. I updated every test
in `dbt/models/schema.yml` (`relationships`, `accepted_values`,
`dbt_utils.accepted_range`) to the new nested form. Not a blocker on its
own — the old syntax still ran, just with a warning — but worth fixing
while already in the file.

## 7. Third `dbt run` — a missing SQL alias

With the catalog and database both correct:

```
$ dbt run
...
1 of 4 OK created sql view model gfw_clean.stg_fishing_events ....... [OK -1 in 3.24s]
2 of 4 ERROR creating sql view model gfw_clean.stg_vessels .......... [ERROR in 1.87s]
3 of 4 OK created sql table model gfw_clean.fact_fishing_event ...... [OK 20 in 6.49s]
4 of 4 SKIP relation gfw_clean.dim_vessel ........................... [SKIP]

[ERROR]: in model stg_vessels (models\staging\stg_vessels.sql)
  Runtime Error
    line 26:19: Column 'entry.selfreportedinfo' cannot be resolved
```

Real progress — `stg_fishing_events` and `fact_fishing_event` both built
successfully, with `fact_fishing_event` landing 20 real rows. `stg_vessels`
was the last thing failing, and `dim_vessel` was skipped only because it
depends on `stg_vessels`, not because of a problem of its own.

The cause: `stg_vessels.sql`'s `FROM` clause referenced the source table
without giving it an alias, while the very next line referenced
`entry.selfreportedinfo` as if that alias existed:

```sql
-- before
from {{ source('gfw_clean', 'dataset_vessels') }}
cross join unnest(entry.selfreportedinfo) as t(self)
```

**Fix:** added the missing alias:

```sql
-- after
from {{ source('gfw_clean', 'dataset_vessels') }} as entry
cross join unnest(entry.selfreportedinfo) as t(self)
```

## 8. Fourth `dbt run` — all models build clean

```
$ dbt run
...
1 of 4 OK created sql view model gfw_clean.stg_fishing_events
2 of 4 OK created sql view model gfw_clean.stg_vessels
3 of 4 OK created sql table model gfw_clean.fact_fishing_event
4 of 4 OK created sql table model gfw_clean.dim_vessel

Completed successfully
```

All four models — two staging views and two mart tables — built without
errors.

## 9. `dbt test`

```bash
dbt test
```

All data tests passed: uniqueness and not-null checks on `dim_vessel`
and `fact_fishing_event`'s primary keys, the `relationships` test
confirming every `fact_fishing_event.vessel_id` has a matching row in
`dim_vessel`, the `accepted_values` check on `event_type`, and the
latitude/longitude range checks.

## Summary of what actually needed to change

| File | Change |
|---|---|
| `~/.dbt/profiles.yml` | `database: AwsDataCatalog` (Data Catalog, not Glue database); `schema: gfw_clean` (the real Glue database) |
| `dbt/models/staging/sources.yml` | `schema: gfw_clean` |
| `dbt/models/staging/stg_vessels.sql` | Added `as entry` alias on the `FROM` clause |
| `dbt/models/schema.yml` | Migrated `relationships` / `accepted_values` / `dbt_utils.accepted_range` to the nested `arguments:` syntax |

With those four changes, the full sequence — `dbt deps`, `dbt debug`,
`dbt run`, `dbt test` — runs clean against the live, deployed pipeline.
