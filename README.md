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
orchestration/        Dagster code
dashboard/            Streamlit dashboard
snowflake_setup/      SQL files to set up Snowflake
docs/                 our data model
dagster_home/         Dagster settings
scripts/              small helper scripts
```

## What you need

- Python 3.12
- uv
- Git
- VS Code with the Snowflake extension
- A user in our Snowflake account (ask Zakaria)
- A Swedavia API key from https://apideveloper.swedavia.se/
- Docker (only for running the containers)

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

dlt loads the data into the `raw` schema. Make a `.env` file in the repo
folder from the template, and fill in your Swedavia key and the Snowflake
values (the comments in the file say how):

```bash
cp .env.example .env
```

`.env` is in `.gitignore`, so your keys never end up in git.

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

Build all models and run all tests:

```bash
dbt build
```

These are our models:

- `src` - cleans the raw tables (`src_arrivals`, `src_departures`,
  `src_airline_codes`, `src_airport_info`). Saved as views in `staging`.
- `fct` - `fct_flights`, one row per arrival or departure. Saved in `warehouse`.
- `dim` - `dim_date`, `dim_airline` and `dim_airport`. Saved in `warehouse`.
- `mart` - `mart_flight_delays`, one table with everything the dashboard needs.
  Saved in `marts`.

We have 33 tests in `models/schema.yml`. They check for example that every
flight has a unique key and that every airline and airport in `fct_flights`
exists in the dimension tables. `dbt build` runs them after each model.

## Known issue: first Wikipedia load

The Wikipedia sources use `write_disposition="replace"`, which runs TRUNCATE
before the table exists. On a brand new schema the first load fails. Set both
resources to `"append"` once, run, then switch back.

## Data model

We use a star schema. The diagram is in `docs/data_model.dbml` (open it in
https://dbdiagram.io).

- `fct_flights` is the fact table. One row is one arrival or one departure at
  a Swedavia airport. It has the scheduled and actual time, the delay in
  minutes and if the flight was delayed or cancelled.
- `dim_airline` - one row per airline. Name from Swedavia, country from
  Wikipedia.
- `dim_airport` - one row per airport. We use it twice: for the Swedavia
  airport and for the airport at the other end of the flight.
- `dim_date` - one row per date, with weekday, week, month, year and if it is
  a weekend.

All four lines in the diagram are one-to-many: one airline, airport or date
has many flights.

## Dagster

Dagster runs the whole pipeline. Start it from the repo folder:

```bash
uv run dagster dev -f orchestration/definitions.py
```

Then open http://127.0.0.1:3000 in your browser.

- Every day at 04:30 UTC Dagster loads the Swedavia data with dlt. That is
  06:30 Swedish summer time and 05:30 in winter.
- Every Monday it loads the Wikipedia data.
- When the Swedavia load is done, a sensor starts dbt and all models are
  built again.
- The schedules and the sensor are on from the start, so you don't have to
  turn them on in the Dagster UI.
- The schedules only run while Dagster is running.

## Dashboard

The dashboard reads from `marts.mart_flight_delays` and logs in as
`streamlit_user`. Make a file `.streamlit/secrets.toml` in the repo folder:

```toml
[connections.snowflake]
account = "<account_identifier>"
user = "streamlit_user"
private_key_file = "/Users/<your_user>/.ssh/snowflake/streamlit_key.p8"
role = "streamlit_reporter"
warehouse = "flights_wh"
database = "flights_db"
schema = "marts"
```

This file is in `.gitignore`. Then start the dashboard:

```bash
uv run streamlit run dashboard/app.py
```

In the sidebar you can choose start and end date, airports and direction
(arrival or departure). The dashboard shows:

- the number of flights, delayed flights, percent delayed, average delay and
  cancelled flights
- delays per airport, per day and per airline

For each chart you can switch between the number of delayed flights and the
percent delayed.

## Docker and Azure

We have two containers, one for Dagster and one for the dashboard. They use
the same `.env` file as in the dlt section, so make sure all values are filled
in. Then build and start both containers:

```bash
docker compose up --build
```

- Dagster is on http://localhost:3000
- The dashboard is on http://localhost:8501

The keys are put in `.env` as text, not as files. When the dashboard container
starts, it makes its own key file and `secrets.toml` from `.env`, so no secrets
are copied into the image.

### Azure

The same two images also run in Azure:

- The images are pushed to an Azure Container Registry. The image names in
  `docker-compose.yml` point to it.
- Dagster runs as an Azure Container App. It is always on, so the schedules
  and the sensor run without anyone's computer being on.
- The dashboard runs as an Azure Web App with a public URL.
- The keys are added as environment variables in Azure, with the same names
  as in `.env`. They are never in the image or in git.

## Things we decided

- We use the 10 airports that Swedavia has in the API: ARN, BMA, GOT, MMX,
  LLA, UME, OSD, VBY, RNB and KRN.
- A flight is delayed if it is more than 15 minutes late. We only count
  flights that have landed or departed.
- Cancelled flights are counted on their own.
- Flights with the status "Deleted" were removed from the schedule, so we
  leave them out.

## Group

- Zakaria Abdullahi
- Marcus Andersson
- Nasser Wahi
