SELECT
	aa.flight_year,
	aa.flight_month,
	aa.flight_date,	-- Date of the flight
	aa.avg_dep_delay_time, -- Calculated for Flights not cancelled with values in FL_DATE,ORIGIN,DEP_DELAY features.
	aa.score as anomaly_score, -- ML Isolation Forest output
	aa.outlier as is_anomaly, -- ML Isolation Forest output
	uf.op_carrier as airline_identifier, -- Airline Identifier
	uf.op_carrier_fl_num as flight_number, -- Flight Number
	aa.origin_airport as origin_airport_code, -- Starting Airport Code	
	uf.dest as destination_airport_code, -- Destination Airport Code
	uf.crs_dep_time as planned_departure_time, --Planned Departure Time
	uf.dep_time as actual_departure_time, -- Actual Departure Time
	uf.dep_delay as total_delay_on_departure, -- Total Delay on Departure in minutes
	uf.cancelled, --Flight Cancelled (1 = cancelled)
	uf.cancellation_code -- Reason for Cancellation of flight: A - Airline/Carrier; B - Weather; C - National Air System; D - Security
FROM dw.airports_departure_anomalies aa
LEFT JOIN spectrum_stage.us_flights_airline_delay_cancellation uf
ON aa.origin_airport = uf.origin AND aa.flight_date = uf.fl_date