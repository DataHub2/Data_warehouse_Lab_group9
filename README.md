# Flight Punctuality Analytics – Group 9

Proof of concept of a modern data stack for a Swedish airport authority.
The pipeline collects arrivals and departures from all Swedavia airports and
enriches them with airline and airport reference data, so that business
stakeholders can analyse **delayed arrivals and departures by airline, airport
and date**.

## Architecture

```
Swedavia FlightInfo API ──┐
Wikipedia: airlines ──────┼── dlt ──▶ RAW ── dbt ──▶ STAGING ──▶ WAREHOUSE ──▶ MARTS ──▶ Streamlit
Wikipedia: airports ──────┘
                 └──────────── orchestrated by Dagster ────────────┘
```

| Layer          | Tool      | Snowflake schema   |
| -------------- | --------- | ------------------ |
| Extract & load | dlt       | `flights_db.raw`   |
| Transform      | dbt       | `flights_db.staging` → `flights_db.warehouse` (dimensions and facts) → `flights_db.marts` |
| Serve          | Streamlit | reads `flights_db.marts` |
| Orchestrate    | Dagster   | –                  |

## Repository structure

```
.
├── data_extract_load/        # dlt: Swedavia and Wikipedia sources + pipeline
│   ├── config.py             # shared settings (airports, dates, URLs)
│   ├── pipeline.py           # entry point for extract and load
│   ├── swedavia_api.py       # Swedavia FlightInfo source (arrivals, departures)
│   └── wikipedia_source.py   # Wikipedia source (airline codes, airports)
├── snowflake_setup/          # Snowflake worksheets, run in numbered order
├── scripts/                  # helper scripts
├── pyproject.toml / uv.lock  # Python dependencies (uv)
└── README.md
```

## Prerequisites

- Python 3.12 and [uv](https://github.com/astral-sh/uv)
- Git
- VS Code with the Snowflake extension
- Access to the group's Snowflake trial account (ask the account owner)
- A Swedavia API subscription key from [apideveloper.swedavia.se](https://apideveloper.swedavia.se/)

## Getting started

```bash
git clone https://github.com/DataHub2/Data_warehouse_Lab_group9.git
cd Data_warehouse_Lab_group9
uv sync
```

`uv sync` creates `.venv` and installs the exact package versions from `uv.lock`.

## Snowflake setup

The whole group develops in **one shared Snowflake trial account**. Everything
that exists in Snowflake is created by the worksheets in `snowflake_setup/`,
so the account can be rebuilt from this repository.

### Run order

Run each file in Snowflake (VS Code extension or Snowsight), in this order:

| Order | File                       | Run as         | Creates                                  |
| ----- | -------------------------- | -------------- | ---------------------------------------- |
| 1     | `01_warehouse.sql`         | SYSADMIN       | warehouse `flights_wh`                   |
| 2     | `02_database_schemas.sql`  | SYSADMIN       | database `flights_db` with `raw`, `staging`, `warehouse`, `marts` |
| 3     | `03_roles.sql`             | USERADMIN      | functional and access roles              |
| 4     | `04_grants.sql`            | SECURITYADMIN  | privileges and role hierarchy            |
| 5     | `05_users.sql`             | USERADMIN / SECURITYADMIN | personal users and service users |

Each file switches to the correct role itself.

### Access control

Roles follow the principle of least privilege. **Access roles** hold the
privileges on a schema; **functional roles** combine access roles and are
granted to users.

| Functional role      | Used by              | Can                                        |
| -------------------- | -------------------- | ------------------------------------------ |
| `dlt_loader`         | `dlt_user`           | write to `raw` (and create dlt's `raw_staging`) |
| `dbt_transformer`    | `dbt_user`           | read `raw`, build `staging`, `warehouse` and `marts` |
| `streamlit_reporter` | `streamlit_user`     | read `marts`                               |
| `developer`          | team members         | everything the three tool roles can do     |

All custom roles roll up to `SYSADMIN`.

### Users

| User             | Type    | Login        | Role                 |
| ---------------- | ------- | ------------ | -------------------- |
| team members     | PERSON  | password + MFA | `developer`        |
| `dlt_user`       | SERVICE | key pair     | `dlt_loader`         |
| `dbt_user`       | SERVICE | key pair     | `dbt_transformer`    |
| `streamlit_user` | SERVICE | key pair     | `streamlit_reporter` |

Programs log in as service users with key pairs instead of passwords.
Snowflake does not allow password login for `TYPE = SERVICE` users.

**Secrets are never stored in this repository.** Passwords and public keys
are set in an unsaved worksheet:

```sql
USE ROLE USERADMIN;
ALTER USER <user> SET PASSWORD = '<temporary_password>' MUST_CHANGE_PASSWORD = TRUE;
ALTER USER <service_user> SET RSA_PUBLIC_KEY = '<public key without header/footer>';
```

### Key pairs for service users

Generate one key pair per tool, outside the repository:

```bash
mkdir -p ~/.ssh/snowflake
```

```bash
for u in dlt dbt streamlit; do openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -nocrypt -out ~/.ssh/snowflake/${u}_key.p8 && openssl rsa -in ~/.ssh/snowflake/${u}_key.p8 -pubout -out ~/.ssh/snowflake/${u}_key.pub; done
```

- `*_key.pub` (public key) is set on the service user in Snowflake.
- `*_key.p8` (private key) stays in `~/.ssh/snowflake/` on every machine that
  runs the pipeline. It is shared privately within the group and is ignored
  by git.

## Extract and load (dlt)

`pipeline.py` loads both sources into the `raw` dataset. By default it writes
local parquet files to `_local_data/` (ignored by git) so the code can be
tested without Snowflake.

```bash
uv run --env-file .env python data_extract_load/pipeline.py
```

```bash
uv run --env-file .env python data_extract_load/pipeline.py --source wikipedia
```

```bash
uv run --env-file .env python data_extract_load/pipeline.py --destination snowflake
```

The Swedavia source reads `SWEDAVIA_API_KEY` from the environment, so `.env`
must contain:

```
SWEDAVIA_API_KEY=<your key>
```

- Flights are loaded with `write_disposition="merge"`, so each run updates
  existing flights and adds new ones. The API only returns the last three days,
  so running daily builds up history.
- Wikipedia reference tables are replaced on every run.

## Data model

_To be added: dimensional model (dbdiagram) and description of facts and dimensions._

## Transformation (dbt)

_To be added._

## Orchestration (Dagster)

_To be added._

## Dashboard (Streamlit)

_To be added._

## Deployment (Docker and Azure)

_To be added._

## Assumptions

- **Airports:** "all available airports in Sweden" is interpreted as the ten
  airports operated by Swedavia and served by the FlightInfo API:
  ARN, BMA, GOT, MMX, LLA, UME, OSD, VBY, RNB, KRN.
- **Delay definition:** _to be decided after data exploration._

## Team

- Zakaria Abdullahi
- Marcus Andersson
- Nasr Wahi
