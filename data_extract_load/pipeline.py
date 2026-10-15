# dlt pipeline

## Main entry point for the extract and load step.
## Pulls from the Swedavia, FlightInfo API and Wikipedia, 
## and loads into the configured destination
## (which fow now is, local parquet, Snowflake once the account is ready).

## Dagster imports source functions directly instead of calling this file,
## the scheduled runs will go through orchestration/definitions.py.
## Same sources, no duplicates. Extraction logic.

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
    pipeline = build_pipeline(destination)

    results = {}
    for name in source_names:
        if name not in SOURCES:
            raise ValueError(f"Unknown source {name!r}. Choose from {sorted(SOURCES)}.")

        # Updated, by way of LLM.
        # Filesystem destination defaults to a gzipped jsonl. 
        # Parquet keeps column types that dlt inferred 
        # and will be readable with pandas directly, 
        # which is the point of a local landing zone.
        load_info = pipeline.run(
            SOURCES[name](),
            loader_file_format="parquet" if destination == "filesystem" else None,
        )
        results[name] = load_info
        print(f"\n--- {name} ---")
        print(load_info)

    return results


def _parse_args():
    parser = argparse.ArgumentParser(description="Load flight punctuality source data.")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        choices=sorted(SOURCES),
        help="Load only this source. Repeatable. Defaults to all.",
    )
    parser.add_argument(
        "--destination",
        default=DEFAULT_DESTINATION,
        help=f"dlt destination. Defaults to {DEFAULT_DESTINATION!r}.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(source_names=args.sources, destination=args.destination)