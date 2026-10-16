-- Cleaned airline codes from Wikipedia (List of airline codes).
-- The table also contains booking systems and other non-airlines,
-- and IATA/ICAO codes are not unique, so it is deduplicated in dim_airline.

with airline_codes as (
    select * from {{ source('raw', 'airline_codes') }}
)

select
    nullif(trim(iata), '')      as iata,
    nullif(trim(icao), '')      as icao,
    airline                     as airline_name,
    country_region              as country
from airline_codes