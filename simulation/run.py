import argparse
import datetime as dt
import json
import time

import dill
import kafka
import kafka.admin
import redis
from river import datasets, linear_model, metrics, neighbors, preprocessing, stream, tree


class colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"


def sleep(td: dt.timedelta):
    if td.seconds > 0:
        time.sleep(td.seconds / args.speed)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=int, nargs="?", default=1)
    args = parser.parse_args()

    # Store model
    model_store = redis.Redis(host="redis", port=6379)
    models = {
        "linear-regression": preprocessing.StandardScaler() | linear_model.LinearRegression(),
        "bayesian-linear-regression": preprocessing.StandardScaler()
        | linear_model.BayesianLinearRegression(),
        "decision-tree": tree.HoeffdingAdaptiveTreeRegressor(),
        "nearest-neighbors": preprocessing.StandardScaler() | neighbors.KNNRegressor(),
    }
    for model_name, model in models.items():
        model_bytes = dill.dumps(model)
        model_store.set(model_name, model_bytes)
        print(f"Uploaded model '{model_name}'")

    # Create topics
    message_bus_admin = kafka.admin.KafkaAdminClient(bootstrap_servers=["redpanda:9092"])
    for topic_name in ["pick-ups", "drop-offs"]:
        # First, delete the topic for idempotency reasons
        try:
            message_bus_admin.delete_topics([topic_name])
        except kafka.errors.UnknownTopicOrPartitionError:
            ...
        topic = kafka.admin.NewTopic(name=topic_name, num_partitions=3, replication_factor=1)
        message_bus_admin.create_topics([topic])
        print(f"Created topic '{topic_name}'")

    # Run simulation
    print(f"Running simulation at speed x{args.speed}")
    message_bus = kafka.KafkaProducer(
        bootstrap_servers=["redpanda:9092"],
        key_serializer=str.encode,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    # Use the first trip's pick-up time as a reference time
    taxis = datasets.Taxis()
    now = next(iter(taxis))[0]["pickup_datetime"]

    for trip_no, trip, duration in stream.simulate_qa(
        taxis, moment="pickup_datetime", delay=lambda _, duration: dt.timedelta(seconds=duration),
    ):
        trip_no = str(trip_no).zfill(len(str(taxis.n_samples)))

        # Taxi trip starts

        if duration is None:

            # Wait
            sleep(trip["pickup_datetime"] - now)
            now = trip["pickup_datetime"]

            # Emit pick-up
            message_bus.send(
                topic="pick-ups",
                key=trip_no,
                value={**trip, "pickup_datetime": trip["pickup_datetime"].isoformat()},
            )

            print(colors.GREEN + f"#{trip_no} pick-up at {now}" + colors.ENDC)
            continue

        # Taxi trip ends

        # Wait
        drop_off_at = trip["pickup_datetime"] + dt.timedelta(seconds=duration)
        sleep(drop_off_at - now)
        now = drop_off_at

        # Emit drop-off
        message_bus.send(
            topic="drop-offs", key=trip_no, value={"drop_off_datetime": drop_off_at.isoformat()},
        )

        # Log drop-off and compare prediction against ground truth
        print(
            colors.BLUE
            + f"#{trip_no} drop-off at {now}, took {dt.timedelta(seconds=duration)}"
            + colors.ENDC
        )
