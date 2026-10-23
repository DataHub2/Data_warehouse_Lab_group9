# Flight Punctuality Analytics

This is our group project in the Data Warehouse course. We build a data
pipeline that collects flight data from Swedish airports and shows how many
arrivals and departures are delayed. You can look at the delays by airline,
by airport and by date.

## How the pipeline works

```
Swedavia API + Wikipedia -> dlt -> Snowflake -> dbt -> Streamlit
```

1. dlt gets flights from the Swedavia API and airline/airport data from
   Wikipedia, and loads it into Snowflake.
2. dbt cleans the data and builds the tables we use for analysis.
3. Streamlit shows a dashboard with the results.
4. Dagster runs everything automatically.

In Snowflake we use one database, `flights_db`, with four schemas:

- `raw` - the data exactly as dlt loads it
- `staging` - cleaned data
- `warehouse` - our dimension and fact tables
- `marts` - the tables the dashboard uses

## Folders

```
data_extract_load/    dlt code (Swedavia and Wikipedia)
data_transformation/  dbt project
snowflake_setup/      SQL files to set up Snowflake
scripts/              small helper scripts
```

## What you need

- Python 3.12
- uv
- Git
- VS Code with the Snowflake extension
- A user in our Snowflake account (ask Zakaria)
- A Swedavia API key from https://apideveloper.swedavia.se/

## Get started

Clone the repo and install the packages:

```bash
git clone https://github.com/DataHub2/Data_warehouse_Lab_group9.git
```

```bash
cd Data_warehouse_Lab_group9
```

```bash
uv sync
```

## Snowflake

We all work in the same Snowflake account. Everything in Snowflake is created
by the SQL files in `snowflake_setup/`. Run them in this order:

1. `01_warehouse.sql` - creates the warehouse `flights_wh`
2. `02_database_schemas.sql` - creates `flights_db` and the four schemas
3. `03_roles.sql` - creates the roles
4. `04_grants.sql` - gives the roles their access
5. `05_users.sql` - creates the users

Each file starts with the right role, for example `USE ROLE SYSADMIN;`.

### Roles

Every tool gets its own role, so it can only do what it needs:

- `dlt_loader` can write to `raw`
- `dbt_transformer` can read `raw` and write to `staging`, `warehouse` and `marts`
- `streamlit_reporter` can only read `marts`
- `developer` is for us in the group and has all three roles above

### Users

- Each of us has our own user with a password. We use the role `developer`.
- dlt, dbt and Streamlit have their own users: `dlt_user`, `dbt_user` and
  `streamlit_user`. They log in with a key file instead of a password.

We never put passwords or keys in the repo. Passwords and public keys are set
directly in Snowflake.

### Key files

The key files are made with this command. You only need it if you set up a new
Snowflake account. Otherwise you get the key files from Zakaria.

```bash
mkdir -p ~/.ssh/snowflake
```

```bash
for u in dlt dbt streamlit; do openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -nocrypt -out ~/.ssh/snowflake/${u}_key.p8 && openssl rsa -in ~/.ssh/snowflake/${u}_key.p8 -pubout -out ~/.ssh/snowflake/${u}_key.pub; done
```

Save the three `.p8` files in `~/.ssh/snowflake/` on your computer. Never add
them to git.

## dlt

dlt loads the data into the `raw` schema. Put your Swedavia key in a `.env`
file in the repo folder:

```
SWEDAVIA_API_KEY=your_key_here
```

Run the pipeline and save the data locally (good for testing):

```bash
uv run --env-file .env python data_extract_load/pipeline.py
```

Run it and load the data into Snowflake:

```bash
uv run --env-file .env python data_extract_load/pipeline.py --destination snowflake
```

The API only has data for the last three days, so we run the pipeline every
day to collect more history.

## dbt

The dbt project is in the folder `data_transformation/`.

First, add this to the file `~/.dbt/profiles.yml` on your computer. If the
file already has something in it, add this at the bottom:

```yaml
data_transformation:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <account_identifier>
      user: dbt_user
      private_key_path: /Users/<your_user>/.ssh/snowflake/dbt_key.p8
      role: dbt_transformer
      warehouse: flights_wh
      database: flights_db
      schema: staging
      threads: 4
```

Change `<account_identifier>` and `<your_user>` to your own values.

Then go into the dbt folder and test the connection:

```bash
cd data_transformation
```

```bash
dbt deps
```

```bash
dbt debug
```

If it says "All checks passed!" it works.

## First load (issues) to a new Snowflake schema

The Wikipedia sources use `write_disposition="replace"`, which issues
TRUNCATE before the table exists. On a brand new schema the first load
fails. Set both resources to `"append"` once, run, then switch back.

## Data model

Coming soon.

## Dagster

Coming soon.

## Dashboard

Coming soon.

## Docker and Azure

Two containers, built from `dockerfile.dwh` (dlt, dbt and Dagster) and
`dockerfile.dashboard` (Streamlit). Run both locally with:

    docker compose up --build

Dagster on port 3000, the dashboard on 8501.

Nothing secret is in the images. Credentials arrive as environment
variables and the dashboard's entrypoint writes `.streamlit/secrets.toml`
at startup. `.env.example` lists every variable, including how to turn a
.p8 key file into a one-line value.

### Deployed on Azure

Both containers run as Azure Container Apps,
with images in an Azure Container Registry. Build and push in one step:

    az acr build --registry flightsacrnasr --image flights-dwh:latest --file dockerfile.dwh .
    az acr build --registry flightsacrnasr --image flights-dashboard:latest --file dockerfile.dashboard .

The Dagster container runs with `--min-replicas 1` so the daemon stays
alive and the schedules actually run as planned. URLs, found in private group chat.

### Things that cost us time

`az containerapp update --set-env-vars` registers variables on the app but
does not restart the replica on an express environment, so the running
container never sees them. `--revision-suffix` is not supported there
either. Deleting and recreating the app is what works.

The Dagster UI has no authentication, Dagster ships without any. 
However, in production it would sit behind private ingress with an identity provider, 
and only the dashboard would be public. For a short-lived course deployment 
we accepted that and will delete the resource group shortly afterwards.

## Things we decided

- We use the 10 airports that Swedavia has in the API: ARN, BMA, GOT, MMX,
  LLA, UME, OSD, VBY, RNB and KRN.
- What counts as a delay: 15-minutes.

## Group

- Zakaria Abdullahi
- Marcus Andersson
- Nasser Abdulwahab
