
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


-- ----------------------------------------------
-- Service users for the tools (key-pair login)
-- Public keys are set in an unsaved worksheet with
-- ALTER USER ... SET RSA_PUBLIC_KEY
-- ----------------------------------------------

USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS dlt_user
    TYPE = SERVICE
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = dlt_loader
    COMMENT = 'Service user for dlt';

CREATE USER IF NOT EXISTS dbt_user
    TYPE = SERVICE
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = dbt_transformer
    COMMENT = 'Service user for dbt';

CREATE USER IF NOT EXISTS streamlit_user
    TYPE = SERVICE
    DEFAULT_WAREHOUSE = flights_wh
    DEFAULT_ROLE = streamlit_reporter
    COMMENT = 'Service user for Streamlit';

USE ROLE SECURITYADMIN;

GRANT ROLE dlt_loader         TO USER dlt_user;
GRANT ROLE dbt_transformer    TO USER dbt_user;
GRANT ROLE streamlit_reporter TO USER streamlit_user;