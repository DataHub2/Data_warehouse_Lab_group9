"""Flight punctuality dashboard for Swedavia airports."""

import streamlit as st

from utils.snowflake_connection import load_flight_delays
from utils.metrics import delay_summary
from utils.charts import MEASURE_OPTIONS, ONE_DAY_MS, PERCENT_OPTION, delay_chart
from utils.filters import apply_sidebar_filters


# Must be the first Streamlit call; wide layout uses the full browser width
st.set_page_config(page_title="Flight Punctuality", layout="wide")

# Responsive layout: column rows become a grid where every card has the same
# width (at least 180 px). Cards that do not fit move to the next row, aligned
# under the ones above.
st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"]{
        display: grid !important;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    }
    div[data-testid="stColumn"] {width: auto !important;}
    </style> 
    """,
    unsafe_allow_html=True,
)

st.title("Flight Punctuality at Swedavia Airports")

# Load on row per flight from MARTS
df = load_flight_delays()

filtered = apply_sidebar_filters(df)

################################################################
# KPI row: headline numbers for the current filter selection
################################################################

# Completed flights have an actual time; only they can be on time or delayed
completed = filtered[filtered["is_completed"]]
delayed = completed[completed["is_delayed"]]

total_flights = len(filtered)
delayed_flights = len(delayed)
cancelled_flights = int(filtered["is_cancelled"].sum())

# Guard against division by zero when no flights in the selection are completed
delay_share = delayed_flights / len(completed) if len(completed) else 0
avg_delay = delayed["delay_minutes"].mean() if delayed_flights else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Number of Flights", f"{total_flights:,}")
kpi2.metric("Delayed flights", f"{delayed_flights:,}")
kpi3.metric("% of flights delayd", f"{delay_share * 100:.1f}")
kpi4.metric("Average delayed (minutes)", f"{avg_delay:.0f}")
kpi5.metric("Cancelled flights", f"{cancelled_flights:,}")

######################################################################
# Delays per aiport: percent or number, split by arrival and departure
######################################################################

st.subheader("Delays per airport")

# One-line definition so stakeholders read the numbers the same way
st.caption(
    "A flight counts as delayed when it is more than 15 minutes late. "
    "Only flight that have arrived or departed are included."
)

# Let the user switch between percent and number of delayed flight

measure = st.radio(
    "Select to view", MEASURE_OPTIONS, horizontal=True, key="airport_measure"
)

# Completed flights, delayed flights and share per airport and direction
by_airport = delay_summary(completed, ["airport_name", "direction"])

# Order airports by overall percent delayed, worst first
airport_order = (
    delay_summary(completed, ["airport_name"])
    .sort_values("delay_share", ascending=False)["airport_name"]
    .tolist()
)

fig = delay_chart(by_airport, "airport_name", measure, color="direction")

# Apply the airport order, specific to this chart
fig.update_xaxes(categoryorder="array", categoryarray=airport_order)

st.plotly_chart(fig, use_container_width=True)


####################################################################
# Delays per day: percent or number, split by arrival and departure
####################################################################

st.subheader("Delay per day")

# The newest day is still in progress, which effects especially the number of flights
st.caption(
    "The latest day is not over yet. Its numbers only include flights that had "
    "arrived or departed when the data was last loaded."
)

# Own key, since Streamlit needs unique keys for identical widgets on one page

day_measure = st.radio(
    "Select to view", MEASURE_OPTIONS, horizontal=True, key="day_measure"
)

# Completed flights, delayed flights and share per date and direction
by_day = delay_summary(completed, ["flight_date", "direction"])

fig_day = delay_chart(by_day, "flight_date", day_measure, color="direction")

# One tick per day, written as a date
fig_day.update_xaxes(dtick=ONE_DAY_MS, tickformat="%Y-%m-%d")

st.plotly_chart(fig_day, use_container_width=True)

#######################################################
# Delays per airline: the 15 airlines with most delays
#######################################################

st.subheader("Delays per airline")
# Minimum completed flights for an airline to be shown
MIN_FLIGHTS = 10
st.caption(
    f"Airlines with fewer than {MIN_FLIGHTS} completed flights are left out, "
    "since a few flights give misleading percentages."
)
airline_measure = st.radio(
    "Show", MEASURE_OPTIONS, horizontal=True, key="airline_measure"
)

# Completed flights, delayed flights and share per airline
by_airline = delay_summary(completed, ["airline_name"])

# Drop small airlines, their percentages are not reliable
by_airline = by_airline[by_airline["flights"] >= MIN_FLIGHTS]

if by_airline.empty:
    st.info(
        f"No airline has at least {MIN_FLIGHTS} completed flights in this selection."
    )
else:
    # Keep the 15 worst airlines for the chosen measure
    sort_column = "delay_share" if airline_measure == PERCENT_OPTION else "delayed"
    top_airlines = by_airline.sort_values(sort_column, ascending=False).head(15)

    fig_airline = delay_chart(
        top_airlines, "airline_name", airline_measure, horizontal=True
    )

    # Worst airline on top instead of at the bottom
    fig_airline.update_yaxes(categoryorder="total ascending")

    st.plotly_chart(fig_airline, use_container_width=True)
