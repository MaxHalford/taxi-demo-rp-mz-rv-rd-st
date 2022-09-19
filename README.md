# Predicting (and learning) taxi trip durations in real-time

This is a self-contained demo using [Redpanda](https://redpanda.com/), [Materialize](https://materialize.com/), [River](https://riverml.xyz/), [Redis](https://redis.io/), and [Streamlit](https://streamlit.io/) to predict taxi trip durations 🔮

The purpose of this contrived example is to demonstrate how the streaming analytics ecosystem can work together 🤝

Each technology has been picked for a particular purpose, but each one could be replaced with an alternative. [Kafka](https://kafka.apache.org/) could replace Redpanda. [Flink](https://flink.apache.org/), [Pinot](https://pinot.apache.org/), or [Bytewax](https://www.bytewax.io/) could stand in for Materialize. You may also want to use a feature store such as [Feast](https://www.tecton.ai/feast/) if that floats your boat. Redis could be replaced with any other storage backend, or even a dedicated model store like [MLflow](https://www.mlflow.org/docs/latest/model-registry.html). A tool other than Metabase could be used for visual monitoring.

## Architecture

<div align="center">
    <img width="80%" src="https://user-images.githubusercontent.com/8095957/190930718-f044416f-f65f-4833-93a0-9a2a4d2036fc.png">
</div>

</br>

🦊 Redpanda acts as a message bus, storing the data produced by the entire system.

🚕 Taxi trips are [simulated](simulation/) with a Python script. An event is sent to Redpanda each time a taxi departs. The duration of the trip is also sent to Redpanda once the taxi arrives at its destination.

🍥 Materialize consumes the pick-up and drop-off topics from Redpanda, and does stream processing on top. It keeps track of the system as a whole, builds aggregate features in real-time, and monitors the model's predictive performance.

🌊 A River model is listening to Materialize for taxi pick-ups. It makes a prediction each time a taxi departs. The prediction is sent to Redpanda, and then gets picked up by Materialize.

🔮 The River model is also listening to Materialize for taxi drop-off. Each time a taxi arrives, Materialize joins the original features with the trip duration. This labelled sample is fed into the River model.

📮 The [inference](inference/) and [learning](learning/) services coordinate with one another by storing the model in a Redis instance. The latter acts as a primitive model store.

💅🏻 Streamlit is used to monitor the overall system in real-time.

🐳 The system is Dockerized, which reduces the burden of connecting the different parts with each other.

## Demo

The first service is in charge of simulating the data stream. For each trip, it first emits an event indicating a taxi has departed. Another event is sent once the taxi arrives. This is all managed by the [`simulation`](simulation) service, which loops over the data at 10 times the actual speed the events occur in the dataset. Before this all happens, the service also uploads some models to Redis, which acts as a model store.

<div align="center">
    <img width="80%" src="screenshots/simulation.png">
</div>

All events are stored in the Redpanda message queue. These then get enriched by Materialize, which computes real-time features and joins them with each taxi departure. The [`inference`](inference) service listens to Materialize with a [`TAIL` query](https://materialize.com/docs/sql/tail/). For every sample, the service loops through each model, generates a prediction, and sends the `(trip_id, model, prediction)` triplet to RedPanda.

<div align="center">
    <img width="80%" src="screenshots/inference.png">
</div>

At this point, there are three topics in RedPanda: `drop_offs`, `pick_ups`, and `predictions`. Materialize is leveraged to join m all on the `trip_id` key they share. This allows measuring the actual trip duration, which can then be compared to each prediction, thereby allowing to monitor the live performance of each model. It's also possible to measure the prediction lag: the elapsed time between when a pick-up event was emitted, and when a prediction was made. This all gets displayed in auto-refreshing Streamlit app.

<div align="center">
    <img width="80%" src="screenshots/monitoring.gif">
</div>

## Running it yourself

Grab the code and run it with [Docker Compose](https://docs.docker.com/compose/):

```sh
# Clone it
git clone https://github.com/MaxHalford/taxi-demo-rp-mz-rv-rd-mb
cd taxi-demo-rp-mz-rv-rd-mb

# Run it
docker-compose up -d
```

Then go to [localhost:8501](http://localhost:8501/) to access the live dashboard.

Here are some useful commands you may use additionally:

```sh
# See what's running
docker stats

# Follow the logs for a particular service
docker compose logs simulation -f
docker compose logs inference -f
docker compose logs learning -f

# See the predictions flowing in
docker exec -it redpanda rpk topic consume predictions --brokers=localhost:9092

# Clean slate
docker compose down --rmi all -v --remove-orphans
```

## Going further

This demo is only way of doing online machine learning. It's also quite narrow, as it's a supervised learning task, which is arguably simpler to reason about than, say, a recommender system. There are a lot of rabbit holes to explore. Here are a bunch of thoughts organised into paragraphs to give some food for thought.

The features `x` used during inference are stored aside -- in the message bus. They are then joined -- thanks to Materialize -- with the label `y` once it arrives. That pair `(x, y)` is fed into the model for learning. This called the "log and wait" technique. You can read more about it from Fennel AI [here](https://blog.fennel.ai/p/real-world-recommendation-systems), from Tecton [here](https://www.tecton.ai/blog/time-travel-in-ml/), and from Faire [here](https://craft.faire.com/building-faires-new-marketplace-ranking-infrastructure-a53bf938aba0).

Materialize is arguably doing most of the work in this setup. It's quite impressive how much you can do with a database and a query language on top. This is even more so true when the database does stream processing. There's many good reasons to push computation into the database. For instance, doing real-time feature engineering with Materialize is much more efficient than doing it in Python. Likewise, it's very easy to do performance monitoring in SQL once you've logged the predictions and the labels. You can read more about this "bundling into the database" idea from Ethan Rosenthal [here](https://www.ethanrosenthal.com/2022/05/10/database-bundling/).

# TODO: reactive vs. proactive, message bus vs. API call
# TODO: listening to Materialize rather than Redpanda
# TODO: feature storage
# TODO: inference/learning sync
# TODO: model selection
# TODO: Scaling, federated learning

## License

This is free and open-source software licensed under the [MIT license](LICENSE).
