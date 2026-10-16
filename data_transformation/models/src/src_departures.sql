-- Cleaned departures from the Swedavia API, one row per flight.
-- Same columns as src_arrivals, so the two can be combined in fct_flights.
-- For departures the other airport is the destination (arrival airport).
--
-- Status codes: ACT (departed), DEL (deleted), SCH (scheduled),
-- CAN (cancelled), SEQ (new estimated time, not departed yet).
-- Only ACT flights have actual_at. DEL flights will be filtered out in fct_flights.

with departures as (
    select * from {{ source('raw', 'departures') }}
)

select
    _load_key                                       as flight_key,
    _event_type                                     as direction,
    to_date(_flight_date)                           as flight_date,
    _airport_iata                                   as airport_iata,
    flight_leg_identifier__arrival_airport_iata     as other_airport_iata,
    arrival_airport_english                         as other_airport_name,
    flight_id                                       as flight_number,
    airline_operator__iata                          as airline_iata,
    airline_operator__icao                          as airline_icao,
    airline_operator__name                          as airline_name,
    di_indicator                                    as traffic_type,
    location_and_status__flight_leg_status          as status_code,
    location_and_status__flight_leg_status_english  as status_text,
    departure_time__scheduled_utc                   as scheduled_at,
    departure_time__estimated_utc                   as estimated_at,
    departure_time__actual_utc                      as actual_at
from departures