# Dagster definitions.py

## Orchestration: dlt loads into RAW, then dbt builds the rest.

## Terminal. Run locally:
##   uv run dagster dev -f orchestration/definitions.py

## Dagster imports the dlt sources directly instead of pipeline.py.
## pipeline.py stays for the manual entry points (local runs), 
## and for testing the sources in isolation.
## Same source functions, no duplicates. Extraction logic.

import sys
from pathlib import Path

import dagster as dg
import dlt
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dlt import DagsterDltResource, dlt_assets

REPO_ROOT = Path(__file__).resolve().parent[1]

# Add the data_extract_load folder to the Python path, 
# so that we can import from it.
# Non-dependent on the working directory.
sys.path.insert(0, str(REPO_ROOT / "data_extract_load"))

from config import PIPELINE_NAME, RAW_DATASET
from swedavia_api import swedavia_source
from wikipedia_source import wikipedia_source

# dlt creates a staging dataset of its own.
# Truncating keeps the warehouse free of leftovers, between runs etc.
dlt.config["load.truncate_staging_dataset"] = True

# dlt assets

dlt_resource = DagsterDltResource()


def _pipeline(name):
    """One dlt pipeline per source, both -> same RAW dataset.

    Separating pipeline names keeps state apart, and helps to have failure 
    in one source that cannot leave the other with pending packages.
    """
    return dlt.pipeline(
        pipeline_name=f"{PIPELINE_NAME}_{name}",
        destination="snowflake",
        dataset_name=RAW_DATASET,
    )


@dlt_assets(dlt_source=swedavia_source(), dlt_pipeline=_pipeline("swedavia"))
def swedavia_load(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


@dlt_assets(dlt_source=wikipedia_source(), dlt_pipeline=_pipeline("wikipedia"))
def wikipedia_load(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


# dbt assets

dbt_project = DbtProject(
    project_dir=REPO_ROOT / "data_transformation",
    profiles_dir=Path.home() / ".dbt",
)

# Produces manifest.json.
# This way, Dagster will learn the model dependencies.
dbt_project.prepare_if_dev()

dbt_resource = DbtCliResource(project_dir=dbt_project)


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# Dagster job

job_swedavia = dg.define_asset_job(
    "job_swedavia", selection=dg.AssetSelection.assets(swedavia_load)
)
job_wikipedia = dg.define_asset_job(
    "job_wikipedia", selection=dg.AssetSelection.assets(wikipedia_load)
)
job_dbt = dg.define_asset_job("job_dbt", selection=dg.AssetSelection.assets(dbt_models))


# Schedules

schedule_swedavia = dg.ScheduleDefinition(
    job=job_swedavia,
    cron_schedule="30 4 * * *",
)

# Reference....
schedule_wikipedia = dg.ScheduleDefinition(
    job=job_wikipedia,
    cron_schedule="40 3 * * 1",
)


# Definitions

## Note to self: dbt models...

defs = dg.Definitions(
    assets=[swedavia_load, wikipedia_load, dbt_models],
    resources={"dlt": dlt_resource, "dbt": dbt_resource},
    jobs=[job_swedavia, job_wikipedia, job_dbt],
    schedules=[schedule_swedavia, schedule_wikipedia],
)