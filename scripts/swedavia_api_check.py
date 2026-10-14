# Swedavia API Check Script

## Answers config.py and swedavia_api.py questions about the Swedavia FlightInfo API v2,
## E.g. which date format the endpoint expects,
## real field names,
## whether actualUtc is populated for the past flights,
## and whether flightLegIdentifier can serve as the merge key.

# Usage: 
## uv run python scripts/swedavia_api_check.py

## SWEDAVIA_API_KEY in .env or environment variable is required.

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
    # Similar to the Swedavia file in data extract, 
    # accept is required. Without it the API answers 400, not 406.
    # Resolved by adding the Accept header to the request.
    return {
        "Ocp-Apim-Subscription-Key": api_key,
        "Accept": "application/json",
    }

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
    """Call the endpoint once per candidate format and report which ones answer 200."""
    working = []

    for label, fmt in DATE_FORMATS.items():
        formatted = probe_date.strftime(fmt)
        url = f"{BASE_URL}/{PROBE_AIRPORT}/{PROBE_ENDPOINT}/{formatted}"

        try:
            response = requests.get(url, headers=_headers(api_key), timeout=30)
        except requests.RequestException as error:
            print(f"  {label:22} {formatted:16} request failed: {error}")
            continue

        status = response.status_code
        note = ""
        if status == 200:
            try:
                count = _get(response.json(), "numberOfFlights")
                note = f"numberOfFlights={count if count is not None else '?'}"
            except ValueError:
                note = "200 but body is not JSON"
            working.append((label, fmt, formatted))

        if status != 200:
            note = response.text[:200].strip()

        print(f"  {label:22} {formatted:16} HTTP {status} {note}")
   
    return working


def describe_structure(payload):
    """Print the top-level keys and one full flight record."""
    print("\n--- top level keys ---")
    for key, value in payload.items():
        kind = type(value).__name__
        if isinstance(value, list):
            print(f"  {key} ({kind}, {len(value)} items)")
        else:
            print(f"  {key} ({kind}) = {value!r}")

    flights = _get(payload, "flights") or []
    if not flights:
        print("\nNo flights in the response - try another date or airport.")
        return

    print(f"\n--- first flight record ({len(flights)} total) ---")
    print(json.dumps(flights[0], indent=2, ensure_ascii=False)[:4000])


def check_time_population(payload):
    """Count populated time fields, status values and distinct leg identifiers.

    The actual count decides how delay is calculated: if actualUtc is mostly
    empty for past flights, the metric cannot rely on it alone.
    """
    flights = _get(payload, "flights") or []
    if not flights:
        return

    counters = {"scheduled": 0, "estimated": 0, "actual": 0}
    statuses = {}
    leg_identifiers = []
    missing_identifiers = 0

    for flight in flights:
        times = _get(flight, "departureTime", "arrivalTime") or {}
        for name, field in (
            ("scheduled", "scheduledUtc"),
            ("estimated", "estimatedUtc"),
            ("actual", "actualUtc"),
        ):
            if _get(times, field):
                counters[name] += 1

        status = _get(_get(flight, "locationAndStatus") or {}, "flightLegStatus")
        statuses[status] = statuses.get(status, 0) + 1

        identifier = _get(flight, "flightLegIdentifier")
        if identifier is None:
            missing_identifiers += 1
        else:
            leg_identifiers.append(json.dumps(identifier, sort_keys=True))

    total = len(flights)
    print(f"\n--- time field population ({total} flights) ---")
    for name, count in counters.items():
        print(f"  {name:10} {count}/{total}")

    print("\n--- flightLegStatus distribution ---")
    for status, count in sorted(statuses.items(), key=lambda item: -item[1]):
        print(f"  {status!r:30} {count}")
    
    # Absent and duplicated are different answers: 
    # One rules the field out, the other means it exists 
    # but needs tweaks/company in the key.
    print("\n--- flightLegIdentifier ---")
    if missing_identifiers:
        print(f"  absent on {missing_identifiers}/{total} flights -> cannot be the key")
    if leg_identifiers:
        present = len(leg_identifiers)
        unique = len(set(leg_identifiers))
        verdict = (
            "usable as unique key"
            if unique == present and not missing_identifiers
            else "NOT unique - keep the composite key"
        )
        print(f"  {unique} distinct values across {present} flights -> {verdict}")


def main():
    load_dotenv()
    api_key = os.getenv("SWEDAVIA_API_KEY")

    if not api_key:
        raise SystemExit("SWEDAVIA_API_KEY is not set. Add it to .env or the environment.")

    # Yesterday, not today. 
    # Past flights are the ones that have actual times.
    probe_date = date.today() - timedelta(days=1)
    print(f"Probing {PROBE_AIRPORT} {PROBE_ENDPOINT} for {probe_date}\n")

    print("--- date format ---")
    working = find_date_format(api_key, probe_date)

    if not working:
        raise SystemExit("\nNo date format accepted. Check that the key is subscribed to FlightInfo v2.")

    label, fmt, formatted = working[0]
    print(f"\nUsing {label} ({formatted}) for the structural probe.")

    url = f"{BASE_URL}/{PROBE_AIRPORT}/{PROBE_ENDPOINT}/{formatted}"
    payload = requests.get(url, headers=_headers(api_key), timeout=30).json()

    describe_structure(payload)
    check_time_population(payload)

    # Beside this script, so that the run does not need to depend on the working directory.
    output_path = Path(__file__).resolve().parent / "swedavia_api_sample.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    print(f"\nFull response written to {output_path}")


if __name__ == "__main__":
    main()