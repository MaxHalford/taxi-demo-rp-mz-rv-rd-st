CREATE VIEW features AS (

    WITH _pick_ups AS (
        SELECT
            *,
            EXTRACT(HOUR FROM pick_up_at) AS pick_up_hour,
            ABS(pick_up_longitude - drop_off_longitude) + ABS(pick_up_latitude - drop_off_latitude) AS l1_distance
        FROM pick_ups
        WHERE trip_id NOT IN (SELECT trip_id FROM predictions)
    ),

    completed_trips AS (
        SELECT
            *,
            EXTRACT(epoch FROM drop_off_at - pick_up_at) AS duration
        FROM drop_offs
        LEFT JOIN _pick_ups USING (trip_id)
    ),

    hourly_features AS (
        SELECT
            pick_up_hour,
            AVG(l1_distance / duration) AS avg_speed_by_hour
        FROM completed_trips
        GROUP BY pick_up_hour
    ),

    cyclic_features AS (
        SELECT
            trip_id,
            COS(2 * 3.1415 * EXTRACT(HOUR FROM pick_up_at) / 24) AS hour_cos,
            SIN(2 * 3.1415 * EXTRACT(HOUR FROM pick_up_at) / 24) AS hour_sin
        FROM _pick_ups
    ),

    distance_features AS (
        SELECT
            trip_id,
            l1_distance
        FROM _pick_ups
    ),

    trip_features AS (
        SELECT
            trip_id,
            passenger_count,
            EXTRACT(ISODOW FROM pick_up_at) IN (6, 7) AS is_weekend
        FROM _pick_ups
    )

    SELECT
        trip_id,
        trip_features.*,
        distance_features.*,
        COALESCE(hourly_features.avg_speed_by_hour, 0) AS avg_speed_by_hour,
        cyclic_features.*
    FROM _pick_ups
    LEFT JOIN trip_features USING (trip_id)
    LEFT JOIN distance_features USING (trip_id)
    LEFT JOIN cyclic_features USING (trip_id)
    LEFT JOIN hourly_features USING (pick_up_hour)
)
