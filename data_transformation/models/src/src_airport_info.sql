-- Cleaned airports from Wikipedia (List of international airports by country).
-- The country is a heading on the page, not a column, so it is not available.
-- location is the city. Smaller airports (e.g. Kiruna, Ronneby) are missing.

with airport_info as (
    select * from {{ source('raw', 'airport_info') }}
)

select
    nullif(trim(iata_code), '')     as iata,
    airport                         as airport_name,
    location                        as city
from airport_info