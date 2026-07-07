Check over each individual task, does the result meet the requirements given by the product owner.
# Does it do, what it needs to be doing?
# Do any errors occur? 
# Are there ways implemented, for preventing those errors?
# Have the errors being handled, after the pipeline was ran again?
# Was the review by another team member done, and correctly?

Example: CSV Data Extraction (Task)
- CSV loads successfully
- Rows converted successfully into Python objects
- No errors occur with mock/sample file


## RFP-1 Setup source control
29/05/2026

- Git repository is created for the Roaming Rhubarbs final project.
- Team members can access the repository.
- Project files are committed to source control.
- Branching workflow is used for team development.
- Changes are pushed to GitHub and visible to the team.
- Work has been reviewed before being marked as Done.

## RFP-2 Agree ways of working
29/05/2026

- Team ways of working are documented in `docs/ways-of-working.md`.
- Communication channels are agreed.
- Daily standup expectations are documented.
- Git strategy and pull request expectations are documented.
- Team working practices are visible to all members.
- Work has been reviewed before being marked as Done.

## RFP-3 Define "definition of done"
29/05/2026

- Definition of Done is documented in `docs/definition-of-done.md`.
- The checklist explains what must be complete before a ticket is marked Done.
- Testing, review, documentation, and approval expectations are included.
- Sprint-level completion expectations are documented.
- Work has been reviewed before being marked as Done.

## RFP-4 Add acceptance criteria to all Sprint 1 tickets
29/05/2026

- Acceptance criteria are documented for Sprint 1 tasks.
- Criteria explain what each task must achieve.
- Criteria include testing and review expectations.
- Criteria are written clearly enough for the team to verify completion.
- Work has been reviewed before being marked as Done.

## RFP-5 Organise team retro
29/05/2026

- Retrospective format is documented in `docs/organise-team-retro.md`.
- Meeting time, duration, location, and lead approach are recorded.
- Retro agenda includes what went well, what did not go well, and actions for next sprint.
- Sprint retro notes are added where available.
- Work has been reviewed before being marked as Done.

## RFP-6 Design schema to model data
29/05/2026

- Database schema is designed for the transformed cafe transaction data.
- Schema includes branches, payment types, products, transactions, and transaction items.
- Primary keys and foreign key relationships are defined.
- Schema design is documented in `docs/schema-design.md`.
- Schema supports the ETL transform output.
- Work has been reviewed before being marked as Done.

## RFP-7 Extract data from CSV file
29/05/2026

- CSV data can be extracted from the Leeds transaction file.
- Rows are converted into Python dictionaries.
- Blank or incomplete rows are handled safely.
- The extractor supports local file reading.
- Extraction logic is covered by tests in `tests/test_extract.py`.
- Work has been reviewed before being marked as Done.

## RFP-8 Add Podman and Adminer containers
29/05/2026

- Local database services are defined in `docker-compose.yaml`.
- PostgreSQL container is configured using environment variables.
- Adminer container is available for local database inspection.
- Database schema is mounted into the PostgreSQL startup folder.
- Local container setup supports the local ETL proof of concept.
- Work has been reviewed before being marked as Done.

## RFP-9 Transform - Remove sensitive data
29/05/2026

- Customer names are removed during transformation.
- Card numbers are removed during transformation.
- Sensitive fields are not returned in transformed output.
- The transform keeps only the fields required for loading.
- Sensitive data removal is covered by tests in `tests/test_transform.py`.
- Work has been reviewed before being marked as Done.

## RFP-10 Create SQL script to generate database
29/05/2026

- SQL schema script exists for creating project database tables.
- The script creates branches, payment_type, products, transactions, and transaction_items.
- Primary key and foreign key relationships are included.
- The schema supports both local loading and Redshift loading.
- The script is stored under `databases/db-scripts/`.
- Work has been reviewed before being marked as Done.

## RFP-11 Transform - Normalise data to match your schema
02/06/2026

- Raw transaction rows are normalised into schema-shaped records.
- Items ordered are split into product and transaction item records.
- Product names, quantities, and prices are separated.
- UUID-style IDs are generated in Python.
- Foreign key relationships are preserved between transformed tables.
- Transform output is covered by tests in `tests/test_transform.py`.
- Work has been reviewed before being marked as Done.

## RFP-12 Write utility code for loading data into database
29/05/2026

- Load utility functions exist in `ETL/load.py`.
- Data loads into tables in foreign key safe order.
- Batch insert logic is used for loading records.
- Database transaction is committed only after all table loads succeed.
- Rollback occurs if an insert fails.
- Load logic is covered by tests in `tests/test_load.py`.
- Work has been reviewed before being marked as Done.

## RFP-13 Connect to the database script
29/05/2026

- Database connection logic exists in `databases/connectdb.py`.
- Local PostgreSQL connection uses environment variables.
- Redshift connection can read configuration from AWS SSM Parameter Store.
- Connection functions are reusable by local ETL and Lambda ETL paths.
- Sensitive connection values are not hard-coded in the main ETL code.
- Work has been reviewed before being marked as Done.

## RFP-14 Convert create SQL script to .sql format instead
02/06/2026

- A standalone `.sql` schema file exists in `databases/db-scripts/`.
- The SQL file contains the active table creation script.
- The old Python schema creation file no longer contains the active schema definition.
- Docker PostgreSQL can initialise using the SQL file.
- Redshift-compatible schema changes are reflected in the SQL script.
- Work has been reviewed before being marked as Done.

## RFP-15 Update Dockerfile to work with the new .sql format
02/06/2026

- Docker setup uses the standalone SQL schema file.
- PostgreSQL initialises tables from `001_create_tables.sql`.
- Python application image installs required dependencies from `requirements.txt`.
- Local ETL can still run through Docker.
- Local proof of concept remains separate from AWS Redshift deployment.
- Work has been reviewed before being marked as Done.

## RFP-16 Testing and Error Handling
02/06/2026

- Unit tests exist for extract, transform, load, and main import behaviour.
- Extract logic handles blank, incomplete, and missing file cases.
- Load logic rolls back if database insert fails.
- Transform logic verifies sensitive data is removed.
- Error handling supports clearer debugging during ETL runs.
- Work has been reviewed before being marked as Done.

## RFP-17 Extract.py only works on one specifically named file
02/06/2026

- Extract logic no longer depends only on one hard-coded CSV filename.
- `get_data()` can use supplied data directly.
- `get_data()` can load from an explicit file path.
- `get_data()` can search for the latest CSV in a directory.
- Missing CSV files raise a clear `FileNotFoundError`.
- Work has been reviewed before being marked as Done.

## RFP-18 Either rename transform.py to Transform.py or update imports
04/06/2026

- Import casing is consistent across the project.
- Code imports match the actual file name used in the `ETL` folder.
- Local execution and Lambda execution use the same import path.
- Tests confirm the transform module can be imported.
- No duplicate transform files are required.
- Work has been reviewed before being marked as Done.

## RFP-19 .env needs to be removed from GitHub and ignored
04/06/2026

- `.env` is listed in `.gitignore`.
- Local secrets are not required to be committed to source control.
- Database credentials are managed through environment variables or AWS SSM.
- Any previously exposed credentials are rotated where necessary.
- Project documentation explains how required environment variables should be supplied.
- Work has been reviewed before being marked as Done.

## RFP-20 Create Skeleton ETL Lambda
05/06/2026

- Lambda function file exists in `lambda/lambda_function.py`.
- Lambda handler entry point is defined.
- Lambda imports shared ETL modules from the project.
- Lambda package includes required source folders and dependencies.
- CloudFormation template defines the Lambda resource.
- Work has been reviewed before being marked as Done.

## RFP-21 Modify ETL Lambda to be called by S3 event
05/06/2026

- S3 bucket is defined for CSV uploads.
- S3 object created events invoke the ETL Lambda.
- Lambda handler reads bucket name and object key from the S3 event.
- Object keys are URL-decoded safely.
- Lambda downloads the uploaded CSV from S3 before processing.
- Work has been reviewed before being marked as Done.

## RFP-22 Modify ETL Lambda to load data into Redshift
05/06/2026

- Lambda extracts CSV data from S3.
- Lambda transforms data using the shared ETL transform logic.
- Lambda retrieves Redshift connection settings from SSM Parameter Store.
- Lambda connects to Redshift using `databases/connectdb.py`.
- Lambda loads transformed records using `ETL/load.py`.
- Lambda timeout and memory settings allow the load to complete.
- Work has been reviewed before being marked as Done.

## RFP-23 Ensure everyone in the team can access AWS
05/06/2026

- Team members have access to the required AWS account or learning environment.
- Required AWS region is agreed as `eu-west-1`.
- Team members can access relevant services such as S3, Lambda, CloudFormation, CloudWatch, SSM, and Redshift.
- Access is sufficient to deploy, test, and inspect the ETL pipeline.
- Team members know where to view Lambda logs in CloudWatch.
- Work has been reviewed before being marked as Done.

## RFP-24 Documentation / flutter
05/06/2026

- Project documentation is updated to describe the implemented pipeline.
- Documentation explains local ETL and AWS Lambda/Redshift paths separately.
- Setup, deployment, and testing notes are clear enough for another team member to follow.
- Known fixes and final working configuration are reflected in the documentation.
- Any unrelated placeholder or unclear documentation is cleaned up where possible.
- Work has been reviewed before being marked as Done.

## RFP-25 Testing and debugging
05/06/2026

- Lambda deployment is tested with a valid Leeds transaction CSV.
- CloudWatch logs show extract and transform stages completing.
- Redshift schema is created before loading data.
- Redshift row counts are checked after the Lambda run.
- Runtime issues such as dependency packaging, SSM key mismatch, schema mismatch, and timeout are resolved.
- Final test confirms data loads successfully into Redshift.
- Work has been reviewed before being marked as Done.

