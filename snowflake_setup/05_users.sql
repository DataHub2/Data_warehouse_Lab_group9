
USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS marcus
    TYPE = PERSON
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = developer
    COMMENT = 'Team member: Marcus';