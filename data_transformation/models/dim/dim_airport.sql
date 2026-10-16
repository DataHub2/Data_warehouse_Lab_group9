-- Airport dimension: one row per airport in the Swedavia data, both the ten
-- Swedavia airports and all origins/destinations.
-- airport_name comes from Swedavia (it is usually the city name, e.g. "Kiruna").
-- city comes from Wikipedia, or Swedavia's name when the airport is missing there
-- (e.g. Kiruna, Ronneby and smaller Swedish airports).
-- Swedavia uses placeholder codes (XXD, XXS, ZZZ = "Unknown") that are kept,
-- because fct_flights points to them.

with flights as (
    select airport_iata, other_airport_iata, other_airport_name from {{ ref('src_arrivals') }}
    union all
    select airport_iata, other_airport_iata, other_airport_name from {{ ref('src_departures') }}
),

swedavia_airports as (
    select distinct airport_iata
    from flights
),

airport_names as (
    select other_airport_iata as airport_iata, max(other_airport_name) as airport_name
    from flights
    group by other_airport_iata
),

all_airports as (
    select airport_iata from swedavia_airports
    union
    select airport_iata from airport_names
),

wikipedia as (
    select iata, max(airport_name) as airport_name, max(city) as city
    from {{ ref('src_airport_info') }}
    where iata is not null
    group by iata
)

select
    all_airports.airport_iata,
    coalesce(airport_names.airport_name, wikipedia.airport_name, all_airports.airport_iata) as airport_name,
    coalesce(wikipedia.city, airport_names.airport_name)                                     as city,
    swedavia_airports.airport_iata is not null                                               as is_swedavia_airport
from all_airports
left join airport_names     on all_airports.airport_iata = airport_names.airport_iata
left join wikipedia         on all_airports.airport_iata = wikipedia.iata
left join swedavia_airports on all_airports.airport_iata = swedavia_airports.airport_iata