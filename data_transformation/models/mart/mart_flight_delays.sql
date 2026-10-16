-- Mart for the dashboard: one row per arrival or departure, with names
-- instead of codes, so flights can be filtered by airline, airport and date.
-- Times are converted to Swedish time (Europe/Stockholm) for display.

with flights as (
    select * from {{ ref('fct_flights') }}
),

airlines as (
    select * from {{ ref('dim_airline') }}
),

airports as (
    select * from {{ ref('dim_airport') }}
),

dates as (
    select * from {{ ref('dim_date') }}
)

select
    flights.flight_key,
    flights.date_key                                                    as flight_date,
    dates.day_name,
    dates.is_weekend,
    flights.direction,
    flights.flight_number,
    flights.traffic_type,

    airlines.airline_code,
    airlines.airline_name,
    airlines.country                                                    as airline_country,

    swedavia_airport.airport_iata                                       as airport_iata,
    swedavia_airport.airport_name                                       as airport_name,
    other_airport.airport_iata                                          as other_airport_iata,
    other_airport.airport_name                                          as other_airport_name,
    other_airport.city                                                  as other_airport_city,

    flights.status,
    convert_timezone('Europe/Stockholm', flights.scheduled_at)::timestamp_ntz as scheduled_at_local,
    convert_timezone('Europe/Stockholm', flights.actual_at)::timestamp_ntz    as actual_at_local,
    flights.actual_at is not null                                       as is_completed,
    flights.delay_minutes,
    flights.is_delayed,
    flights.is_cancelled

from flights
left join airlines                       on flights.airline_code       = airlines.airline_code
left join airports as swedavia_airport   on flights.airport_iata       = swedavia_airport.airport_iata
left join airports as other_airport      on flights.other_airport_iata = other_airport.airport_iata
left join dates                          on flights.date_key           = dates.date_key