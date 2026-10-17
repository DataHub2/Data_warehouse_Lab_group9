"""Shared chart building for the dashboard."""

import pandas as pd
import plotly.express as px


# Options for the "Show" buttons ,written once so the buttons and the
# check against them can never differ through a typo

PERCENT_OPTION = "% of flights delayed"
COUNT_OPTION = "Number of delayed flights"
MEASURE_OPTIONS = [PERCENT_OPTION, COUNT_OPTION]

# One day in milliseconds, the unit Plotly uses for distances on a date axis
ONE_DAY_MS = 24 * 60 * 60 * 1000

# Axis and hower labels used by every charts

LABELS = {
    "airport_name": "Airport",
    "airline_name": "Airline",
    "flight_date": "Date",
    "directions": "Direction",
    "flights": "Completed flights",
    "delayed": COUNT_OPTION,
    "delay_share": PERCENT_OPTION,
}


def delay_chart(
    summary: pd.DataFrame,
    category: str,
    measure: str,
    color: str | None = None,
    horizontal: bool = False,
):
    """Bar chart of delays per category, as percent or number of delayed flights."""
    value = "delay_share" if measure == PERCENT_OPTION else "delayed"

    # Horizontal bars swap the axis: values on x, categories on y
    x, y = (value, category) if horizontal else (category, value)

    fig = px.bar(
        summary,
        x=x,
        y=y,
        color=color,
        barmode="group",
        orientation="h" if horizontal else "v",
        hover_data={"flights": True, "delayed": True, "delay_share": ":.1%"},
        labels=LABELS,
    )

    # Percent axis as 20% instead of 0.2
    if measure == PERCENT_OPTION:
        if horizontal:
            fig.update_xaxes(tickformat=".0%")
        else:
            fig.update_yaxes(tickformat=".0%")

    return fig
