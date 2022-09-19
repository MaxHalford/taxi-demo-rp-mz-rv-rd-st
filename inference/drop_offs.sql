CREATE MATERIALIZED SOURCE drop_offs_src
    FROM KAFKA BROKER 'redpanda:9092' TOPIC 'drop-offs'
        KEY FORMAT BYTES
        VALUE FORMAT BYTES
        INCLUDE KEY AS trip_id, TIMESTAMP AS ts;

CREATE VIEW drop_offs_raw AS (
    SELECT
        ts AS received_at,
        CONVERT_FROM(trip_id, 'utf8') AS trip_id,
        CAST(CONVERT_FROM(data, 'utf8') AS JSONB) AS trip
    FROM drop_offs_src
);

CREATE VIEW drop_offs AS (
    SELECT
        received_at,
        trip_id,
        CAST(trip ->> 'drop_off_datetime' AS TIMESTAMP) AS drop_off_at
    FROM drop_offs_raw
)
