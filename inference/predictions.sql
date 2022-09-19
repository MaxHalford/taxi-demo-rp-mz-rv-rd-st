CREATE MATERIALIZED SOURCE predictions_src
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'predictions'
  KEY FORMAT BYTES
  VALUE FORMAT BYTES
  INCLUDE KEY AS trip_model, TIMESTAMP AS ts;

CREATE VIEW predictions_raw AS (
    SELECT
        ts AS received_at,
        CONVERT_FROM(trip_model, 'utf8') AS trip_model,
        CAST(CONVERT_FROM(data, 'utf8') AS JSONB) AS prediction
    FROM predictions_src
);

CREATE VIEW predictions AS (
    SELECT
        received_at,
    	SPLIT_PART(trip_model, '#', 1) AS trip_id,
    	SPLIT_PART(trip_model, '#', 2) AS model,
    	CAST(prediction ->> 'features' AS JSONB) AS features,
    	CAST(prediction ->> 'prediction' AS FLOAT) AS prediction
    FROM predictions_raw
)
