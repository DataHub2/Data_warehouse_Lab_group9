"""Loads dashboard data from Snowflake. Knows nothing about charts or layout."""

from pathlib import Path

import pandas as pd
import streamlit as st

# SQL files live in dashboard/queries, one file per query

QUERIES_DIR = Path(__file__).resolve().parents[1] / "queries"

# Cache results for 10 minutes so every filter click does not hit Snowflake
CACHE_SECONDS = 600


def load_flight_delays() -> pd.DataFrame:
    """Reurn one row per flight from MARTS, with lowercase column names."""
    sql = (QUERIES_DIR / "flight_delays.sql").read_text(encoding="utf-8")

    # st.connection reads [connections.snowflake] from .streamlit/sectrets.toml
    conn = st.connection("snowflake")
    df = conn.query(sql, ttl=CACHE_SECONDS)

    # Snowflake returns uppercase column names; lowercase matches the rest of the code
    df.columns = df.columns.str.lower()
    return df
