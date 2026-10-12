----------------------------------------------------------------
-- Creates all custom roles. Run as USERADMIN.
-- Grants between roles and on objects are set in 04_grants.sql
----------------------------------------------------------------

USE ROLE USERADMIN;

-- Functional roles: one per tool, plus developer for team members.
CREATE ROLE IF NOT EXISTS dlt_loader
    COMMENT = 'Functional role for dlt. Loads source data into RAW.';

CREATE ROLE IF NOT EXISTS dbt_transformer
    COMMENT = 'Functional role for dbt. Reads RAW, builds STAGING and MARTS.';

CREATE ROLE IF NOT EXISTS streamlit_reporter
    COMMENT = 'Functional role for Streamlit. Reads MARTS for the dashboard.';

CREATE ROLE IF NOT EXISTS developer
    COMMENT = 'Functional role for team members. Inherits all tool roles';

-- Access roles: one per schema and privilege level, granted to functional roles.
CREATE ROLE IF NOT EXISTS wh_usage
    COMMENT = 'Access role. Usage on flights_wh, used by all tool roles';

CREATE ROLE IF NOT EXISTS raw_rw
    COMMENT = 'Access role. Read and write in RAW, used by dlt_loader';

CREATE ROLE IF NOT EXISTS raw_r
    COMMENT = 'Access role. Read in RAW, used by dbt_transformer';

CREATE ROLE IF NOT EXISTS staging_rw
    COMMENT = 'Access role. Read and write in STAGING, used by dbt_transformer';

CREATE ROLE IF NOT EXISTS marts_rw
    COMMENT = 'Access role. Read and write in MARTS, used by dbt_transformer';

CREATE ROLE IF NOT EXISTS marts_r
    COMMENT = 'Access role. Read in MARTS, used by streamlit_reporter';