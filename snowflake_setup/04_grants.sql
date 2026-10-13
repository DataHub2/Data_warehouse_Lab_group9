-----------------------------------------------------------
-- Gants on objects and between roles. Run as SECURITYADMIN
-- Requires 01_warehouse, 02_database_schemas and 03_roles.
-----------------------------------------------------------

USE ROLE SECURITYADMIN;

-- ----------------------------------------------
-- Privileges on objects to access roles
-- ----------------------------------------------

-- wh_usage: run queries on the shared warehouse
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE wh_usage;

-- raw_rw: dlt creates tables in RAW and its own RAW_STAGING schema
GRANT USAGE ON DATABASE flights_db TO ROLE raw_rw;
GRANT CREATE SCHEMA ON DATABASE flights_db TO ROLE raw_rw;
GRANT USAGE ON SCHEMA flights_db.raw TO ROLE raw_rw;
GRANT CREATE TABLE ON SCHEMA flights_db.raw TO ROLE raw_rw;

-- raw_r: dbt reads RAW
GRANT USAGE ON DATABASE flights_db TO ROLE raw_r;
GRANT USAGE ON SCHEMA flights_db.raw TO ROLE raw_r;
GRANT SELECT ON ALL TABLES IN SCHEMA flights_db.raw TO ROLE raw_r;
GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.raw TO ROLE raw_r;

-- staging_rw: dbt builds STAGING
GRANT USAGE ON DATABASE flights_db TO ROLE staging_rw;
GRANT USAGE ON SCHEMA flights_db.staging TO ROLE staging_rw;

GRANT CREATE TABLE ON SCHEMA flights_db.staging TO ROLE staging_rw;

GRANT CREATE VIEW ON SCHEMA flights_db.staging TO ROLE staging_rw;


-- warehouse_rw: dbt builds dimensions and facts in WAREHOUSE
GRANT USAGE ON DATABASE flights_db TO ROLE warehouse_rw;
GRANT USAGE ON SCHEMA flights_db.warehouse TO ROLE warehouse_rw;
GRANT CREATE TABLE ON SCHEMA flights_db.warehouse TO ROLE warehouse_rw;
GRANT CREATE VIEW ON SCHEMA flights_db.warehouse TO ROLE warehouse_rw;

-- marts_rw: dbt builds MARTS
GRANT USAGE ON DATABASE flights_db TO ROLE marts_rw;

GRANT USAGE ON SCHEMA flights_db.marts TO ROLE marts_rw;

GRANT CREATE TABLE ON SCHEMA flights_db.marts TO ROLE marts_rw;

GRANT CREATE VIEW ON SCHEMA flights_db.marts TO ROLE marts_rw;

-- marts_r: Streamlit reads MARTS
GRANT USAGE ON DATABASE flights_db TO ROLE marts_r;
GRANT USAGE ON SCHEMA flights_db.marts TO ROLE marts_r;
GRANT SELECT ON ALL TABLES IN SCHEMA flights_db.marts TO ROLE marts_r;
GRANT SELECT ON ALL VIEWS IN SCHEMA flights_db.marts TO ROLE marts_r;

GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.marts TO ROLE marts_r;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA flights_db.marts TO ROLE marts_r;

---------------------------------------------
-- Access roles to tool roles
---------------------------------------------

-- dlt_loader: loads into RAW
GRANT ROLE wh_usage TO ROLE dlt_loader;
GRANT ROLE raw_rw TO ROLE dlt_loader;

-- dbt_transformer: reads RAW, builds STAGING, WAREHOUSE and MARTS
GRANT ROLE wh_usage TO ROLE dbt_transformer;
GRANT ROLE raw_r TO ROLE dbt_transformer;

GRANT ROLE staging_rw TO ROLE dbt_transformer;

GRANT ROLE marts_rw TO ROLE dbt_transformer;

-- streamlit_reporter: reads MARTS
GRANT ROLE wh_usage TO ROLE streamlit_reporter;
GRANT ROLE marts_r TO ROLE streamlit_reporter;

----------------------------------------
-- Tool roles to developer and SYSADMIN
----------------------------------------

-- developer inherits all tool roles
GRANT ROLE dlt_loader TO ROLE developer;

GRANT ROLE dbt_transformer TO ROLE developer;

GRANT ROLE streamlit_reporter TO ROLE developer;

-- everything rolls up to SYSADMIN
GRANT ROLE developer TO ROLE SYSADMIN;

GRANT ROLE dlt_loader TO ROLE SYSADMIN;

GRANT ROLE dbt_transformer TO ROLE SYSADMIN;

GRANT ROLE streamlit_reporter TO ROLE SYSADMIN;

