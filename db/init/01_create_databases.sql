CREATE DATABASE auth_db;
CREATE DATABASE market_db;
CREATE DATABASE analysis_db;
CREATE DATABASE portfolio_db;

\c auth_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c market_db
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit;

\c analysis_db
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit;

\c portfolio_db
CREATE EXTENSION IF NOT EXISTS timescaledb;