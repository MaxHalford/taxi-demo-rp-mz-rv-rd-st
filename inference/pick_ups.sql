CREATE MATERIALIZED SOURCE pick_ups_src
    FROM KAFKA BROKER 'redpanda:9092' TOPIC 'pick-ups'
        KEY FORMAT BYTES
        VALUE FORMAT BYTES
        INCLUDE KEY AS trip_id, TIMESTAMP AS ts;

CREATE VIEW pick_ups_raw AS (
    SELECT
        ts AS received_at,
        CONVERT_FROM(trip_id, 'utf8') AS trip_id,
        CAST(CONVERT_FROM(data, 'utf8') AS JSONB) AS trip
    FROM pick_ups_src
);

CREATE VIEW pick_ups AS (
    SELECT
        received_at,
        trip_id,
        CAST(trip ->> 'pickup_datetime' AS TIMESTAMP) AS pick_up_at,
        CAST(trip ->> 'passenger_count' AS INT) AS passenger_count,
        CAST(trip ->> 'pickup_longitude' AS FLOAT) AS pick_up_longitude,
        CAST(trip ->> 'pickup_latitude' AS FLOAT) AS pick_up_latitude,
        CAST(trip ->> 'dropoff_longitude' AS FLOAT) AS drop_off_longitude,
        CAST(trip ->> 'dropoff_latitude'  AS FLOAT) AS drop_off_latitude
    FROM pick_ups_raw
)
