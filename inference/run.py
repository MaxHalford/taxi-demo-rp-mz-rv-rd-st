import datetime as dt
import json

import dill
import kafka
import kafka.admin
import psycopg
import redis

"""
We first create the views which consume the data from the topics. There is one view for pick-ups,
one for drop-offs, and one for predictions.
"""

dsn = "postgresql://materialize@materialize:6875/materialize?sslmode=disable"
conn = psycopg.connect(dsn)
conn.autocommit = True

with conn.cursor() as cur:
    for source in ("predictions", "pick_ups", "drop_offs"):
        try:
            cur.execute(f"DROP SOURCE {source}_src CASCADE;")
        except Exception as e:
            print(e)

        with open(f"{source}.sql") as f:
            for q in f.read().split(";"):
                cur.execute(q)

"""
Next we define a view holding the trips for which a prediction has to be made.
"""

with conn.cursor() as cur:
    with open("features.sql") as f:
        cur.execute(f.read())

# Let's query the view to see what it contains. That way we can associate each feature with a name.

conn.autocommit = False
with conn.cursor() as cur:
    cur.execute("SHOW COLUMNS FROM features")
    schema = cur.fetchall()
    columns = ["mz_timestamp", "mz_diff"] + [c[0] for c in schema]

"""
Create predictions topic where we will write the predictions.
"""

message_bus_admin = kafka.admin.KafkaAdminClient(bootstrap_servers=["redpanda:9092"])
# First, delete the topic for idempotency reasons
topic_name = "predictions"
try:
    message_bus_admin.delete_topics([topic_name])
except kafka.errors.UnknownTopicOrPartitionError:
    ...
topic = kafka.admin.NewTopic(name=topic_name, num_partitions=3, replication_factor=1)
message_bus_admin.create_topics([topic])
print(f"Created topic '{topic_name}'")
message_bus = kafka.KafkaProducer(
    bootstrap_servers=["redpanda:9092"],
    key_serializer=str.encode,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

"""
Now we can listen to the "inference queue" and make a prediction for every trip.
"""

conn = psycopg.connect(dsn)
models_last_retrieved_at = dt.datetime.min
trip_ids_seen = set()
model_store = redis.Redis(host="redis", port=6379)

with conn.cursor() as cur:
    for row in cur.stream("TAIL features"):

        # We only want to make predictions for trips that have not been seen before
        trip_features = dict(zip(columns, row))
        del trip_features["mz_timestamp"]
        del trip_features["mz_diff"]
        if (trip_id := trip_features.pop("trip_id")) in trip_ids_seen:
            continue
        trip_ids_seen.add(trip_id)

        # Refresh models every 30 seconds
        if (now := dt.datetime.now()) - models_last_retrieved_at > dt.timedelta(seconds=30):
            models = {
                model_name: dill.loads(model_store.get(model_name))
                for model_name in map(bytes.decode, model_store.scan_iter())
            }
            models_last_retrieved_at = now
            print("Refreshed models")

        # Make predictions for each model
        for model_name, model in models.items():
            predicted_duration = model.predict_one(trip_features)
            message_bus.send(
                topic="predictions",
                key=f"{trip_id}#{model_name}",
                value={"features": trip_features, "prediction": predicted_duration},
            )
