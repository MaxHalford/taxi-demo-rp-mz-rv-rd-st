import datetime as dt
import dill
import psycopg
from river import compose
import redis

"""
Load the models.
"""

model_store = redis.Redis(host="redis", port=6379)
models = {
    model_name: dill.loads(model_store.get(model_name))
    for model_name in map(bytes.decode, model_store.scan_iter())
}

"""
Create a view to define the learning queue.
"""

dsn = "postgresql://materialize@materialize:6875/materialize?sslmode=disable"
conn = psycopg.connect(dsn)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute("""
    CREATE VIEW learning_queue AS (

        WITH completed_trips AS (
            SELECT
                *,
                EXTRACT(epoch FROM drop_off_at - pick_up_at) AS duration
            FROM drop_offs
            LEFT JOIN pick_ups USING (trip_id)
        )

        SELECT
            trip_id,
            model,
            features,
            duration
        FROM predictions
        INNER JOIN completed_trips USING (trip_id)
    )
    """)

# Let's query the view to see what it contains. That way we can associate each feature with a name.

conn.autocommit = False
with conn.cursor() as cur:
    cur.execute("SHOW COLUMNS FROM learning_queue")
    schema = cur.fetchall()
    columns = ['mz_timestamp', 'mz_diff'] + [c[0] for c in schema]

"""
Loop forever and update the models.
"""

conn = psycopg.connect(dsn)
models_last_dumped_at = dt.datetime.min

with conn.cursor() as cur:
    for row in cur.stream("TAIL learning_queue"):

        # Dump models every 30 seconds
        if (now := dt.datetime.now()) - models_last_dumped_at > dt.timedelta(seconds=30):
            for model_name, model in models.items():
                model_bytes = dill.dumps(model)
                model_store.set(model_name, model_bytes)
                print(f"Uploaded model '{model_name}'")
            models_last_dumped_at = now

        # Teach the model
        sample = dict(zip(columns, row))
        trip_id = sample["trip_id"]
        model = models[sample["model"]]
        x = sample["features"]
        y = sample["duration"]
        print(f'Learning on #{trip_id} with {sample["model"]}')
        with compose.warm_up_mode():
            model.learn_one(x, y)
