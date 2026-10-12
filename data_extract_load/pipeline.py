import argparse
import os

import dlt

from config import (
    DEFAULT_DESTINATION,
    LOCAL_PARQUET_PATH,
    PIPELINE_NAME,
    STAGING_DATASET,
)

from wikipedia_source import wikipedia_source
