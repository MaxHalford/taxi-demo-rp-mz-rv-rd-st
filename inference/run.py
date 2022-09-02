import psycopg

dsn = "postgresql://materialize@materialize:6875/materialize?sslmode=disable"
conn = psycopg.connect(dsn)
conn.autocommit = True

with conn.cursor() as cur:
    try:
        cur.execute("DROP SOURCE departures_src CASCADE;")
    except Exception:
        ...

    cur.execute("""

CREATE MATERIALIZED SOURCE departures_src
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'departures'
  KEY FORMAT BYTES
  VALUE FORMAT BYTES
ENVELOPE UPSERT;

""")

    cur.execute("""

CREATE VIEW departures_raw AS (
    SELECT
        CONVERT_FROM(key0, 'utf8') AS trip_id,
        CAST(CONVERT_FROM(data, 'utf8') AS JSONB) AS trip
    FROM departures_src
);

""")

    cur.execute("""

CREATE VIEW departures AS (
    SELECT
        trip_id,
        trip ->> 'pickup_datetime' AS pickup_datetime
    FROM departures_raw
);

    """)

# with conn.cursor() as cur:
#     cur.execute("SHOW VIEWS")
#     print(cur.fetchall())

conn = psycopg.connect(dsn)

with conn.cursor() as cur:
    for row in cur.stream("TAIL departures"):
        print(row)
