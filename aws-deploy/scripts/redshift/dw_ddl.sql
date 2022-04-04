CREATE SCHEMA IF NOT EXISTS dw;
CREATE TABLE IF NOT EXISTS  dw.airports_departure_anomalies (
	origin_airport TEXT NOT NULL,
    avg_dep_delay_time FLOAT NULL,
    flight_year INTEGER NULL,
    flight_month INTEGER NULL,
    flight_date DATE NOT NULL,
    score FLOAT NULL,
    outlier TEXT NULL,
    date_time_dag_run TIMESTAMP
);