# RoamingRhubarbsFinalProject
This is an official repository for the final project on Generation UK, for Roaming Rhubarbs team. 

# Roaming Rhubarbs — Café ETL Pipeline

This repository contains the final graduation project for the Generation UK Data Engineering Bootcamp, built by Team Roaming Rhubarbs.

The pipeline ingests raw café transaction data (`CSV` format containing timestamps, locations, customer details, basket items, payment methods, and card numbers), strips away sensitive information, normalizes the dataset, and loads it into a relational database.

---

## ## 1. Pipeline Architecture

The project features a *unified code architecture* supporting two parallel execution tracks. Both environments share the exact same `ETL/` modules and database logic, enforcing DRY (Don't Repeat Yourself) principles.

```
                 ┌─────────────────────┐
   CSV upload →  │   S3: CsvBucket     │
                 └─────────┬───────────┘
                           │ s3:ObjectCreated:*
                           ▼
                 ┌─────────────────────┐
                 │  Lambda: ETLLambda  │
                 │  lambda_function.py │
                 └─────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ETL.Extract        ETL.transform        ETL.load
  (parse CSV text)   (clean + normalise)  (batch insert)
                           │
                           ▼
                 ┌─────────────────────┐
                 │   Amazon Redshift   │
                 │ (creds via SSM)     │
                 └─────────────────────┘

```

### Execution Environments

* **Local Proof of Concept (PoC):** Driven manually or via `main.py` utilizing a containerized **PostgreSQL** instance.
* **Cloud Production Pipeline:** An **AWS Lambda** function triggered automatically by **Amazon S3** object uploads, targeting **Amazon Redshift**.

---

## ## 2. Relational Database Schema

The architecture decomposes raw transaction logs into five highly normalized tables using `UUID` (`VARCHAR(36)`) keys. The definitions are managed via `databases/db-scripts/001_create_tables.sql`.

| Table | Purpose | Relationships |
| --- | --- | --- |
| **`branches`** | Tracks café physical locations | Referenced by `transactions` |
| **`payment_type`** | Valid payment types (Cash, Card, etc.) | Referenced by `transactions` |
| **`products`** | Unique menu items and price combinations | Referenced by `transaction_items` |
| **`transactions`** | Core transactional data (1 row per checkout) | Foreign Keys to `branches`, `payment_type` |
| **`transaction_items`** | Detailed basket line items per transaction | Foreign Keys to `transactions`, `products` |

> 💡 For detailed documentation regarding data types and constraint logic, please refer to [docs/schema-design.md](https://www.google.com/search?q=docs/schema-design.md).

---

## ## 3. Repository Directory Layout

```text
RoamingRhubarbsFinalProject/
├── ETL/                             # Shared ETL Core Core Logic
│   ├── Extract.py                   # CSV parsing (handles files & string streams)
│   ├── transform.py                 # PII stripping, cleaning, and normalization
│   ├── load.py                      # Batched database execution operations
│   └── __init__.py
├── databases/                       # Database Configurations
│   ├── connectdb.py                 # Core connection hub (Postgres & Redshift)
│   ├── create_database.py           # [DEPRECATED] Superseded by SQL scripts
│   └── db-scripts/
│       ├── 001_create_tables.sql    # DDL schema definition file
│       └── ssm.example.json         # Reference payload layout for AWS SSM
├── lambda/                          # AWS Serverless Environment
│   └── lambda_function.py           # Lambda entry point & event handler
├── tests/                           # Robust PyTest automation suite
├── docs/                            # Agile management & process documentations
├── docker-compose.yaml              # Local ecosystem (Postgres + Adminer + ETL App)
├── Dockerfile                       # Python application image build step
├── main.py                          # Local runtime pipeline runner
├── requirements.txt                 # Application Python dependencies
├── etl-stack.yml                    # CloudFormation: Core Lambda Infrastructure
├── deployment-stack.yml             # CloudFormation: Deployment artifacts bucket
└── deploy.sh                        # Automation bash script for AWS publishing

```

---

## ## 4. Local Quickstart (Docker Proof of Concept)

### Prerequisites

* **Docker & Docker Compose** installed locally.
* **Python 3.x** (only required if running natively outside containers).

### Step 1: Environment Setup

Create a `.env` file in your project root using the configuration layout below.

```env
POSTGRES_HOST=localhost
POSTGRES_DB=roamingrhubarbs
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5433

```

### Step 2: Build & Start Containers

Execute the following docker command to launch the database engine, visual interface, and run the entry-point script automatically:

```bash
docker compose up --build

```

**This configuration orchestrates:**

1. A **PostgreSQL 16** instance seeded instantly with `001_create_tables.sql`.
2. An **Adminer UI** available directly on `http://localhost:8080` for live database inspection.
3. An internal runtime of `main.py` which extracts, transforms, and loads the most recently modified native `.csv` file dropped into your local project root directory.

### Native Execution (Without Docker)

If you wish to interact with the code base directly via local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate       # On Windows use: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest

```

---

## ## 5. AWS Cloud Production Infrastructure

### Deployment Overview

The Cloud architecture utilizes infrastructure-as-code via **AWS CloudFormation** mapping to the `eu-west-1` (Ireland) region.

Running `./deploy.sh` completely automates:

1. **Deployment Stack Generation:** Provisions a private deployment S3 bucket to store raw build items.
2. **Package Bundling:** Bundles application dependencies (`psycopg2-binary`, `boto3`, `python-dotenv`), local `ETL/` structures, and target database subfolders into an active `lambda.zip` deployment asset.
3. **ETL Stack Generation:** Spins up `CsvBucket`, constructs the core `ETLLambda` targeting a configured VPC, and provisions necessary strict resource-level permission profiles.

### Pre-Deployment Requirements

Before executing the deployment bash automation script, confirm that:

* Your local machine has an active profile configured pointing to target IAM permissions (Default: `KalebDE`).
* An active IAM execution role is configured at: `arn:aws:iam::660759886369:role/lambda-execution-role`.
* An **AWS SSM SecureString** parameter named `roaming_rhubarb_redshift_settings` contains your functional production Redshift credentials in the structure described within `databases/db-scripts/ssm.example.json`.

```bash
chmod +x deploy.sh
./deploy.sh

```

---

## ## 6. Automated Testing Framework

This repository includes comprehensive test coverage using **PyTest**. It verifies the complete transformation loop to prevent regression issues.

To run the complete test suite locally, run:

```bash
pytest -v

```

### Test Suite Focus Breakdown

* **`test_extract.py`:** Evaluates string stream processing, malformed headers, blank line skips, and graceful file absence failures.
* **`test_transform.py`:** Strict validations tracking proper identification and deletion of sensitive PII, string parsing within the items array, and accurate relational normalization logic.
* **`test_load.py`:** Validates data batch-chunking thresholds, target transactional executions, and automated error recovery rollback patterns.

---

## ## 7. Mandatory Security Protocols ⚠️

> 🛑 **CRITICAL NOTICE:** Secrets and local environment files (`.env`, `ssm.json`) containing real-world infrastructure parameters must never be checked into version control tracking.

### Remediation Blueprint

If sensitive infrastructure parameters or unencrypted passwords were leaked in historic branches or older git snapshots:

1. Add explicit local ignore pathways instantly:
```bash
echo ".env" >> .gitignore
echo "databases/db-scripts/ssm.json" >> .gitignore

```


2. Purge cached references and configurations entirely from tracking:
```bash
git rm --cached .env
git rm --cached databases/db-scripts/ssm.json

```


3. Use specialized cleanup utilities like **BFG Repo-Cleaner** or `git filter-repo` to permanently strip historic footprints from git tree structures before making the repository public.
4. **Immediately rotate all live passwords** across local and production resources that were previously committed to tracking.

---

## ## 8. Agile Delivery & Project Governance

This platform was designed, engineered, and shipped using a disciplined, two-sprint agile delivery methodology.

* **Sprint 1:** Delivered the functional localized proof-of-concept utilizing Docker, localized PostgreSQL constraints, base automated tests, and core functional transformations.
* **Sprint 2:** Migrated capabilities directly into standard AWS serverless architecture (S3 event triggering, cross-network Lambda execution mappings, Secure Cloud SSM Parameter Store lookup patterns, and infrastructural CloudFormation script assembly).

For deep contextual information on delivery processes, refer to the project administrative documentation guides:

* ways-of-working.md
* definition-of-done.md
* organise-team-standup.md
* organise-team-retro.md