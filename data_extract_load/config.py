# config.py

## Shared configuration for the extraction layer of the flight punctuality analytics project.
## Secrets will live in .env / secrets.toml.

import os
from datetime import date, timedelta
from pathlib import Path

# Swedavia API

SWEDAVIA_BASE_URL = "https://api.swedavia.se/flightinfo/v2"

# NOT yet verified against the live API.
# REFERENCE. For now, we assume that the API uses the same date format as the Swedavia website.
# Run scripts/swedavia... to find the format.
SWEDAVIA_DATE_FORMAT = "%Y-%m-%d"

# Two FlightInfo endpoints. 
# Key = the dlt table name and the event_type column,
# arrivals and departures to stay distinguishable after union in dbt.
FLIGHT_ENDPOINTS = ("arrivals", "departures")

# All airports -> by Swedavia and served by FlightInfo v2.
# IATA airport codes, as used by the API.
SWEDISH_AIRPORTS = (
    "ARN",  # Stockholm Arlanda
    "BMA",  # Stockholm Bromma
    "GOT",  # Göteborg Landvetter
    "MMX",  # Malmö
    "LLA",  # Luleå
    "UME",  # Umeå
    "OSD",  # Åre Östersund
    "VBY",  # Visby
    "RNB",  # Ronneby
    "KRN",  # Kiruna
)

# Here, extract data covering the past three days 
# (including the date when you extract data) and all available airports in Sweden.
LOOKBACK_DAYS = 3

# Requests per airport, per date, per endpoint.
# Example: 10 airports x 3 days x 2 endpoints = 60 calls per full run.
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_MAX_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 2


def extraction_dates(reference_date=None, lookback_days=LOOKBACK_DAYS):
    """Returning dates to extract. Oldest first.

    + Reference date itself, so lookback_days=3 yields
    [e.g., today - 2, today - 1, today...].
    """
    reference_date = reference_date or date.today()
    offsets = range(lookback_days - 1, -1, -1)
    return [reference_date - timedelta(days=offset) for offset in offsets]


def format_api_date(value):
    """Format: Date for the FlightInfo URL path."""
    return value.strftime(SWEDAVIA_DATE_FORMAT)


def swedavia_api_key():
    """Read the subscription key, rather it fail than sending back None."""
    api_key = os.getenv("SWEDAVIA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SWEDAVIA_API_KEY -> add it to .env locally,"
            "or, container environment (Azure)."
        )
    return api_key


# Wikipedia

# Reference data:
WIKIPEDIA_SOURCES = {
    "airline_codes": "https://en.wikipedia.org/wiki/List_of_airline_codes",
    "airport_info": "https://en.wikipedia.org/wiki/List_of_international_airports_by_country",
}


# dlt pipeline

PIPELINE_NAME = "flight_punctuality"
RAW_DATASET = "raw"

# The default destination is filesystem
DEFAULT_DESTINATION = os.getenv("DLT_DESTINATION", "filesystem")

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PARQUET_PATH = os.getenv("DLT_LOCAL_PATH") or (REPO_ROOT / "_local_data").as_uri()