import time
import psycopg
import streamlit as st

st.set_page_config(
    page_title="Monitoring",
    page_icon="📊",
    layout="wide",
)

st.title('Live monitoring')

dsn = "postgresql://materialize@materialize:6875/materialize?sslmode=disable"
conn = psycopg.connect(dsn)
conn.autocommit = True

placeholder = st.empty()
prev_perf = {}

while True:
    with conn.cursor() as cur:
        cur.execute("""
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
        """)
        perf = dict(cur.fetchall())

        with placeholder.container():

            columns = st.columns(len(perf))

            for (model_name, mae), col in zip(perf.items(), columns):
                col.metric(
                    model_name,
                    f"{mae:.2f}",
                    delta=f"{mae - prev_perf[model_name]:+.2f}" if prev_perf else None,
                    delta_color="inverse"
                )
            prev_perf = perf

    time.sleep(1)
