-- One row per flight from the flat mart. Columns listed explicitly so the 
-- dashboard does not break if dbt add columns to the table.

SELECT
    flight_date,
    day_name,
    direction,
    traffic_type,
    airline_code,
    airline_name,
    airport_iata,
    airport_name,
    status,
    is_completed,
    delay_minutes,
    is_delayed,
    is_cancelled
FROM flights_db.marts.mart_flight_delays;