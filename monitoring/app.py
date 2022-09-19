import time
import psycopg
import streamlit as st

st.set_page_config(
    page_title="Monitoring",
    page_icon="📊",
    layout="wide",
)

st.title('Live monitoring')
placeholder = st.empty()

dsn = "postgresql://materialize@materialize:6875/materialize?sslmode=disable"
conn = psycopg.connect(dsn)
conn.autocommit = True

# We define the views before entering the loop for performance reasons. Materialize will keep the
# views in memory and update them incrementally.

with conn.cursor() as cur:
    cur.execute("""
    CREATE OR REPLACE VIEW model_perf AS (
        WITH completed_trips AS (
            SELECT
                trip_id,
                EXTRACT(epoch FROM drop_off_at - pick_up_at) AS duration
            FROM drop_offs
            LEFT JOIN pick_ups USING (trip_id)
        )

        SELECT
            model,
            AVG(ABS(prediction - duration)) AS mean_absolute_error
        FROM predictions
        INNER JOIN completed_trips USING (trip_id)
        GROUP BY 1
    )
    """)

with conn.cursor() as cur:
    cur.execute("""
    CREATE OR REPLACE VIEW ops_perf AS (
        WITH prediction_times AS (
            SELECT trip_id, MAX(received_at) AS received_at
            FROM predictions
            GROUP BY trip_id
        )

        SELECT
            AVG(EXTRACT(EPOCH FROM pt.received_at - pu.received_at)) AS prediction_lag,
            COUNT(do.drop_off_at) AS trips_completed,
            COUNT(*) - COUNT(do.drop_off_at) AS trips_in_progress
        FROM pick_ups pu
        LEFT JOIN drop_offs do USING (trip_id)
        LEFT JOIN prediction_times pt USING (trip_id)
    )
    """)

prev_model_perf = {}

while True:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM model_perf")
        model_perf = dict(cur.fetchall())

        cur.execute("SELECT * FROM ops_perf")
        ops_perf = dict(zip((desc[0] for desc in cur.description), cur.fetchone()))
        if ops_perf['prediction_lag'] is not None:
            ops_perf['prediction_lag'] = f"{ops_perf['prediction_lag']:.2f}s"

        with placeholder.container():

            # Display operational metrics
            if ops_perf:
                st.header('⚡ Operational metrics')
                columns = st.columns(len(model_perf))
                for (metric, value), col in zip(ops_perf.items(), columns):
                    col.metric(metric, value)

            # Display the performance of each model
            if model_perf:
                st.header('🎯 Model performance')
                columns = st.columns(len(model_perf))
                for (model_name, mae), col in zip(model_perf.items(), columns):
                    col.metric(
                        model_name,
                        f"{mae:.2f}s",
                        delta=f"{mae - prev_model_perf[model_name]:+.2f}" if prev_model_perf else None,
                        delta_color="inverse"
                    )
                prev_model_perf = model_perf

    time.sleep(1)
