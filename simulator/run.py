import argparse
import datetime as dt
import json
import time

import dill
import kafka
import kafka.admin
import redis
from river import datasets
from river import linear_model
from river import preprocessing
from river import metrics
from river import stream

DOCKER_HOST = '127.0.0.1'
RP_PORT = 9092
RD_PORT = 6379

class colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"

def sleep(td: dt.timedelta):
    if td.seconds > 0:
        time.sleep(td.seconds / args.speed)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("speed", type=int, nargs="?", default=1)
    args = parser.parse_args()

    # Store model
    model_store = redis.Redis(host=DOCKER_HOST, port=RD_PORT)
    models = {
        'super-vanilla-model': preprocessing.StandardScaler() | linear_model.LinearRegression()
    }
    for model_name, model in models.items():
        model_bytes = dill.dumps(model)
        model_store.set(model_name, model_bytes)
        print(f"Uploaded model '{model_name}'")

    # Create topics
    message_queue_admin = kafka.admin.KafkaAdminClient(bootstrap_servers=[f"{DOCKER_HOST}:{RP_PORT}"])
    for topic_name in ['departures', 'arrivals']:
        # First, delete the topic for idempotency reasons
        try:
            message_queue_admin.delete_topics([topic_name])
        except kafka.errors.UnknownTopicOrPartitionError:
            ...
        topic = kafka.admin.NewTopic(name=topic_name, num_partitions=3, replication_factor=1)
        message_queue_admin.create_topics([topic])
        print(f"Created topic '{topic_name}'")

    # Run simulation
    print(f"Running simulation at speed x{args.speed}")
    message_queue = kafka.KafkaProducer(
        bootstrap_servers=[f"{DOCKER_HOST}:{RP_PORT}"],
        key_serializer=str.encode,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    # Use the first trip's departure time as a reference time
    taxis = datasets.Taxis()
    now = next(iter(taxis))[0]["pickup_datetime"]

    for trip_no, trip, duration in stream.simulate_qa(
        taxis,
        moment="pickup_datetime",
        delay=lambda _, duration: dt.timedelta(seconds=duration),
    ):
        trip_no = str(trip_no).zfill(len(str(taxis.n_samples)))

        # Taxi trip starts

        if duration is None:

            # Wait
            sleep(trip["pickup_datetime"] - now)
            now = trip["pickup_datetime"]

            # Emit departure
            message_queue.send(
                topic="departures",
                key=trip_no,
                value={**trip, "pickup_datetime": trip["pickup_datetime"].isoformat()}
            )

            print(colors.GREEN + f"#{trip_no} departs at {now}" + colors.ENDC)
            continue

        # Taxi trip ends

        # Wait
        arrival_time = trip["pickup_datetime"] + dt.timedelta(seconds=duration)
        sleep(arrival_time - now)
        now = arrival_time

        # Emit arrival
        message_queue.send(
            topic="arrivals",
            key=trip_no,
            value={"arrival_datetime": arrival_time.isoformat()}
        )

        # Log arrival and compare prediction against ground truth
        print(
            colors.BLUE
            + f"#{trip_no} arrives at {now}, took {dt.timedelta(seconds=duration)}"
            + colors.ENDC
        )
