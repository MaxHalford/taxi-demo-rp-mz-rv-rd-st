# taxis-rp-mz-rv-rd-mb

## Architecture

<div  align="center">
    <img width="80%" src="https://user-images.githubusercontent.com/8095957/187788485-4d38c15c-8ac4-4294-b3b9-63297ac91071.png">
</div>
</br>

🐼 Redpanda acts as a message bus, storing the data produced by the entire system.

🚕 A taxi simulation is run with a Python script. An event is sent to Redpanda each time a taxi departs. The duration of the trip is also sent to Redpanda once the taxi arrives at its destination.

🍥 Materialize consumes the event and label topics from Redpanda, and does stream processing on top. It keeps track of the system, builds aggregate features in real-time, and monitors the model's predictive performance.

🌊 A River model is listening to Materialize for taxi departures. It makes a prediction each time a taxi departs. The prediction is then sent to Redpanda, and then gets picked up by Materialize.

🔮 The River model is also listening to Materialize for taxi arrivals. Each time a taxi arrives, Materialize joins the original features with the trip duration. This labelled sample is fed into the River model.

📮 The inference and learning parts coordinate each other by storing the model in a Redis instance. The latter acts as a primitive model store.

💅🏻 Metabase is used to monitor the overall system in real-time -- actually, the dashboard is refreshed every 5 seconds, which is good enough.

🐳 The system is Dockerized, which reduces the burden of connecting the different parts with each other.

## Running it

First, grab the code and run it with [Docker Compose](https://docs.docker.com/compose/).

```sh
# Clone it
git clone https://github.com/MaxHalford/taxi-demo-rp-mz-rv-rd-mb
cd taxi-demo-rp-mz-rv-rd-mb

# Run it
docker-compose up -d

# See what's running
docker-compose ps
```

Next, run the simulation script.

```py
# Optionally, use a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r simulator/requirements.txt

# Run the simulation, optionally with a speed-up factor
python simulator/run.py --speed 10
```

This will:

1. Create necessary Redpanda topics
2. Upload a River model to Redis
3. Loop through River's [taxis trips dataset](https://riverml.xyz/0.11.1/api/datasets/Taxis/)
4. Send the events in their arrival order to Redpanda
