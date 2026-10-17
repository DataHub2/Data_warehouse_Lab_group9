"""Sidebar filters for the dashboard."""

import pandas as pd
import streamlit as st


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Show the filters in the sidebar and return only the rows the user selected.

    Stops the page with a message when the selection is invalid or empty.
    """

    st.sidebar.header("Filters")

    # Date: two seperate fields, first day and last day
    # Limited to the dates that exist in the date, so no empty days can picked
    min_date, max_date = df["flight_date"].min(), df["flight_date"].max()

    start_date = st.sidebar.date_input(
        "Start date", value=min_date, min_value=min_date, max_value=max_date
    )
    end_date = st.sidebar.date_input(
        "End date", value=max_date, min_value=min_date, max_value=max_date
    )

    # A start date after the end date gives no flights and tell the user why
    if start_date > end_date:
        st.warning("Start date must be on or before the end date.")
        st.stop()

    # Airport: options come from the data itself
    airports = sorted(df["airport_name"].unique())
    selected_airports = st.sidebar.multiselect(
        "Airport", airports, placeholder="All airports"
    )

    # Direction: both, arrivals only or departure only
    direction = st.sidebar.radio("Direction", ["All", "arrival", "departure"])

    # Apply the filters
    # Keep only rows within the date range and at the selected airports
    filtered = df[df["flight_date"].between(start_date, end_date)]

    # Airport filter only applies when the user has picked at least on airport
    if selected_airports:
        filtered = filtered[filtered["airport_name"].isin(selected_airports)]

    # Direction: "All" keeps both arrivals and departures
    if direction != "All":
        filtered = filtered[filtered["direction"] == direction]

    # Stop early with a message instead of rendering empty charts
    if filtered.empty:
        st.warning("No flights match the selected filters.")
        st.stop()

    return filtered
