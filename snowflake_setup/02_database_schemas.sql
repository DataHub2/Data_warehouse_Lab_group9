-- setup database

USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS flights_db;

CREATE SCHEMA IF NOT EXISTS flights_db.staging;

CREATE SCHEMA IF NOT EXISTS flights_db.raw;

CREATE SCHEMA IF NOT EXISTS flights_db.marts;
