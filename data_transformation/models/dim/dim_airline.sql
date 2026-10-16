-- Airline dimension: one row per airline that appears in the Swedavia data.
-- Name and codes come from Swedavia. Country comes from Wikipedia, matched on
-- ICAO only. IATA codes are reused by several airlines on Wikipedia and gave
-- wrong matches (e.g. Nyxair and FROST Air), so they are not used.
-- ICAO codes are not unique on Wikipedia either, so max() picks one row per code.

with flights as (
    select airline_iata, airline_icao, airline_name from {{ ref('src_arrivals') }}
    union all
    select airline_iata, airline_icao, airline_name from {{ ref('src_departures') }}
),

airlines as (
    select
        coalesce(nullif(airline_iata, ''), airline_icao)  as airline_code,
        max(airline_icao)                                  as airline_icao,
        max(airline_name)                                  as airline_name
    from flights
    group by airline_code
),

wiki_by_icao as (
    select icao, max(country) as country
    from {{ ref('src_airline_codes') }}
    where icao is not null
    group by icao
)

select
    airlines.airline_code,
    airlines.airline_icao,
    airlines.airline_name,
    wiki_by_icao.country
from airlines
left join wiki_by_icao on airlines.airline_icao = wiki_by_icao.icao