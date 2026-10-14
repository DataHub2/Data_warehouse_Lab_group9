# Swedavia API

## Source for the Swedavia FlightInfo API v2, 
## for arrivals and departures at Swedish airports.

## Records will land close to raw and left for dbt to clean.

import hashlib
import time

import dlt
import requests

from config import (
    FLIGHT_ENDPOINTS,
    REQUEST_BACKOFF_SECONDS,
    REQUEST_MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    SWEDAVIA_BASE_URL,
    SWEDISH_AIRPORTS,
    extraction_dates,
    format_api_date,
    swedavia_api_key,
)


# Helpers


def _get(mapping, *names):
    """Case-insensitive key lookup: the docs say FlightId, the API may say flightId."""

    if not isinstance(mapping, dict):
        return None

    lowered = {key.lower(): value for key, value in mapping.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return None


def _fetch_flights(endpoint, airport, api_date, api_key):
    """Call one endpoint for one airport and one date.

    Returns a list of flight records, or an empty list if the endpoint returns 404.
    """
    url = f"{SWEDAVIA_BASE_URL}/{airport}/{endpoint}/{format_api_date(api_date)}"
    # Accept is REQUIRED, tip from course repo: without it the API answers 400, not 406.
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Accept": "application/json",
    }
    last_error = None
    for attempt in range(1, REQUEST_MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)

            if response.status_code == 404:
                return []

            # 429 and 5xx are worth retrying. 4xx below that is not.
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)

            response.raise_for_status()
            return _get(response.json(), "flights") or []

        except requests.RequestException as error:
            last_error = error
            if attempt < REQUEST_MAX_RETRIES:
                time.sleep(REQUEST_BACKOFF_SECONDS * attempt)

    raise RuntimeError(f"Failed to fetch {url} after {REQUEST_MAX_RETRIES} attempts: {last_error}")


def _load_key(flight, endpoint, airport, api_date):
    """Deterministic key for merge loading.

    Built from airport, endpoint, date, flightId and scheduledUtc. Now, IF the
    API's own flightLegIdentifier turns out to be unique, then use that instead.
    """
    times = _get(flight, "departureTime", "arrivalTime") or {}
    parts = (
        airport,
        endpoint,
        format_api_date(api_date),
        str(_get(flight, "flightId") or ""),
        str(_get(times, "scheduledUtc") or ""),
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


# Resources


def _flight_resource(endpoint):
    """One dlt resource for an endpoint."""

    @dlt.resource(
        name=endpoint,
        write_disposition="merge",
        primary_key="_load_key",
    )
    def resource(api_key=None):
        # Read the key from the environment, not dlt.secrets.value: 
        # that "sentinel" (fact check) makes dlt resolve it from its own config providers 
        # and raise before this fallback ever runs.
        # -> breaks .env flow used locally and environment variables that may be used later.
        api_key = api_key or swedavia_api_key()

        for api_date in extraction_dates():
            for airport in SWEDISH_AIRPORTS:
                for flight in _fetch_flights(endpoint, airport, api_date, api_key):
                    # Request context, per-flight body does not carry.
                    flight["_airport_iata"] = airport
                    flight["_event_type"] = endpoint.rstrip("s")
                    flight["_flight_date"] = format_api_date(api_date)
                    flight["_load_key"] = _load_key(flight, endpoint, airport, api_date)
                    yield flight

    return resource


@dlt.source(name="swedavia")
def swedavia_source():
    """FlightInfo endpoints as one dlt source."""
    return [_flight_resource(endpoint)() for endpoint in FLIGHT_ENDPOINTS]