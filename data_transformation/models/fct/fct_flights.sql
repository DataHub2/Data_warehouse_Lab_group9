-- Fact table: one row per arrival or departure at a Swedavia airport.
-- Deleted flights (DEL) are removed, they were never real flights.
-- Delays are only calculated for completed flights (actual_at exists).
-- Domestic flights between two Swedavia airports appear twice (one departure,
-- one arrival), so flight_key is built from the flight leg + direction.

with arrivals as (
    select * from {{ ref('src_arrivals') }}
),

departures as (
    select * from {{ ref('src_departures') }}
),

flights as (
    select * from arrivals
    union all
    select * from departures
)

select
    {{ dbt_utils.generate_surrogate_key(['flights.flight_key', 'flights.direction']) }} as flight_key,
    flights.flight_key                                        as flight_leg_key,
    coalesce(nullif(airline_iata, ''), airline_icao)          as airline_code,
    airport_iata,
    other_airport_iata,
    to_date(convert_timezone('UTC', scheduled_at))            as date_key,
    direction,
    flight_number,
    status_code                                               as status,
    traffic_type,
    scheduled_at,
    actual_at,

    case
        when actual_at is not null
            then datediff('minute', scheduled_at, actual_at)
    end                                                       as delay_minutes,

    case
        when actual_at is not null
            then datediff('minute', scheduled_at, actual_at)
                 > {{ var('delay_threshold_minutes', 15) }}
    end                                                       as is_delayed,

    status_code = 'CAN'                                       as is_cancelled

from flights
where status_code != 'DEL'