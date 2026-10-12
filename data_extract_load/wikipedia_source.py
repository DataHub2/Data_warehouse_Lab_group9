# Wikipedia source

## Reference data for the airline and airport dimensions.

import re
from io import StringIO

import dlt
import pandas as pd
import requests

from config import REQUEST_TIMEOUT_SECONDS, WIKIPEDIA_SOURCES

# Excerpt from the Wikipedia User-Agent policy, by way of LLM:
# Wikimedia's User-Agent policy requires a descriptive header naming the tool
# and how to reach its author. A blank one is blocked outright and
# non-descriptive library defaults may be.
# https://meta.wikimedia.org/wiki/User-Agent_policy
REQUEST_HEADERS = {
    "User-Agent": (
        "data-warehouse-lab-group9/0.1 "
        "(https://github.com/DataHub2/Data_warehouse_Lab_group9)"
    )
}


# Helpers


def _normalise_column(name):
    """Wikipedia table header, into a usable column name."""
    name = str(name)
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    return name.strip("_").lower()


def _normalise_columns(columns):
    """Header row, keeping every column distinct."""
    seen = set()
    names = []

    for column in columns:
        base = _normalise_column(column) or "column"
        name = base
        suffix = 2
        while name in seen:
            name = f"{base}_{suffix}"
            suffix += 1

        seen.add(name)
        names.append(name)

    return names


def _read_tables(url, min_columns):
    """Read every HTML table, then keep the ones wide enough to matter.

    Changed the way the page is fetched with requests rather than handing 
    the URL to read_html. Wikipedia 403 for requests.
    """
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text), flavor="lxml")

    kept = []
    for table in tables:
        if table.shape[1] < min_columns:
            continue
        table.columns = _normalise_columns(table.columns)
        kept.append(table)

    if not kept:
        raise RuntimeError(f"No table with at least {min_columns} columns found at {url}")

    return kept


def _records(tables):
    """Convert kept tables into dlt-ready dicts."""
    combined = pd.concat(tables, ignore_index=True)
    combined = combined.astype(object).where(pd.notna(combined), None)
    return combined.to_dict(orient="records")


# Resources


@dlt.resource(name="airline_codes", write_disposition="replace")
def airline_codes():
    """IATA and ICAO airline codes with operator names.

    Replace rather than merge. The page is a complete list. The latest
    scrape = no history worth keeping.
    """
    tables = _read_tables(WIKIPEDIA_SOURCES["airline_codes"], min_columns=4)
    yield from _records(tables)


@dlt.resource(name="airport_info", write_disposition="replace")
def airport_info():
    """International airports by country.

    Page has one table per country, all with the same shape, 
    into a single resource.
    """
    tables = _read_tables(WIKIPEDIA_SOURCES["airport_info"], min_columns=3)
    yield from _records(tables)


@dlt.source(name="wikipedia")
def wikipedia_source():
    """(2)Reference tables as one dlt source."""
    return [airline_codes(), airport_info()]