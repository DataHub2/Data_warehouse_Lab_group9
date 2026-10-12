
USE ROLE USERADMIN;


-- Marcus
CREATE USER IF NOT EXISTS marcus
    TYPE = PERSON
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = developer
    COMMENT = 'Team member: Marcus';



-- Nasser 

CREATE USER IF NOT EXISTS nasr
    TYPE = PERSON
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = developer
    COMMENT = 'Team member: Nasr';





USE ROLE SECURITYADMIN;

GRANT ROLE developer TO USER marcus;
GRANT ROLE developer TO USER nasr;


SHOW GRANTS OF ROLE developer;