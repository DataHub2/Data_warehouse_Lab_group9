# dlt pipeline

## Main entry point for the extract and load step.
## Pulls from the Swedavia, FlightInfo API and Wikipedia, 
## and loads into the configured destination
## (which fow now is, local parquet, Snowflake once the account is ready).

## Terminal. Run:
##   uv run python data_extract_load/pipeline.py
##   uv run python data_extract_load/pipeline.py --source wikipedia
##   uv run python data_extract_load/pipeline.py --destination snowflake

import argparse
import os

import dlt

from config import (
    DEFAULT_DESTINATION,
    LOCAL_PARQUET_PATH,
    PIPELINE_NAME,
    RAW_DATASET,
)
from swedavia_api import swedavia_source
from wikipedia_source import wikipedia_source

# dlt creates a staging dataset of its own. 
# Truncating keeps the warehouse free of leftovers, between runs etc.
dlt.config["load.truncate_staging_dataset"] = True

SOURCES = {
    "swedavia": swedavia_source,
    "wikipedia": wikipedia_source,
}


def build_pipeline(destination=DEFAULT_DESTINATION):
    """Create the dlt pipeline for the chosen destination: local parquet or Snowflake."""
    if destination == "filesystem":
        # Point to the local parquet landing zone at the repo
        # instead of requiring a bucket_url in secrets.toml
        # for what is a temporary local setup.
        os.environ.setdefault(
            "DESTINATION__FILESYSTEM__BUCKET_URL", LOCAL_PARQUET_PATH
        )

    return dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=destination,
        dataset_name=RAW_DATASET,
    )


def run(source_names=None, destination=DEFAULT_DESTINATION):
    """Load one or more sources + return the load info for each and every one."""
    source_names = source_names or list(SOURCES)