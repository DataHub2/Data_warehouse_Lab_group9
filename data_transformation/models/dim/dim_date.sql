-- Date dimension: one row per date that exists in fct_flights.
-- date_key is the scheduled date in UTC, same as in fct_flights.

with dates as (
    select distinct date_key
    from {{ ref('fct_flights') }}
)

select
    date_key,
    dayofweekiso(date_key)          as day_of_week,
    dayname(date_key)               as day_name,
    dayofweekiso(date_key) >= 6     as is_weekend,
    weekiso(date_key)               as week_number,
    month(date_key)                 as month,
    year(date_key)                  as year
from dates