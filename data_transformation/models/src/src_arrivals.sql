with arrivals as (
    select * from {{ source('raw', 'arrivals') }}
)

select
    _load_key                                       as flight_key,
    _event_type                                     as direction,
    to_date(_flight_date)                           as flight_date,
    _airport_iata                                   as airport_iata,
    flight_leg_identifier__departure_airport_iata   as other_airport_iata,
    departure_airport_english                       as other_airport_name,
    flight_id                                       as flight_number,
    airline_operator__iata                          as airline_iata,
    airline_operator__icao                          as airline_icao,
    airline_operator__name                          as airline_name,
    di_indicator                                    as traffic_type,
    location_and_status__flight_leg_status          as status_code,
    location_and_status__flight_leg_status_english  as status_text,
    arrival_time__scheduled_utc                     as scheduled_at,
    arrival_time__estimated_utc                     as estimated_at,
    arrival_time__actual_utc                        as actual_at
from arrivals