# Dagster definitions.py

## Orchestration

## Run locally:
##   uv run


## Dagster imports the dlt sources directly instead of pipeline.py.

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