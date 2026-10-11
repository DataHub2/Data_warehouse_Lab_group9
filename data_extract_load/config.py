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