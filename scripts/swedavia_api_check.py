# Swedavia API Check Script



import json
import os
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.swedavia.se/flightinfo/v2"
PROBE_AIRPORT = "ARN"
PROBE_ENDPOINT = "departures"

# Docs say "yyyymm-dd", which is not a real format.
# Try plausible readings and check answers.
DATE_FORMATS = {
    "yyyy-mm-dd": "%Y-%m-%d",
    "yymmdd": "%y%m%d",
    "yyyymmdd": "%Y%m%d",
    "yyyy-mm-ddThh:mm": "%Y-%m-%dT00:00",
}


def _headers(api_key):
    return {"Ocp-Apim-Subscription-Key": api_key}


def _get(mapping, *names):
    """Case-insensitive key lookup: Docs say FlightId, while the API might say flightId."""
    if not isinstance(mapping, dict):
        return None

    lowered = {key.lower(): value for key, value in mapping.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return None


def find_date_format(api_key, probe_date):
    """Call the endpoint per candidate..."""
    working = []

    for label, fmt in DATE_FORMATS.items():
        formatted = probe_date.strftime(fmt)
        url = f"{BASE_URL}/{PROBE_AIRPORT}/{PROBE_ENDPOINT}"

        try:
            response = requests.get()
        except requests.RequestException as error:
            print()
            continue
