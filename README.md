# taxis-rp-mz-rv-mb

## Architecture

<div  align="center">
    <img width="70%" src="https://user-images.githubusercontent.com/8095957/187721317-59c5b2e3-2414-45b8-a8d4-985e13f0c25a.png">
</div>

🐼 Redpanda acts as a message bus, storing the data produced by the entire system.

🚕 A taxi simulation is run with a Python script. An event is sent to Redpanda each time a taxi departs. The duration of the trip is also sent to Redpanda once the taxi arrives at its destination.

🍥 Materialize consumes the event and label topics from Redpanda, and does stream processing on top. It keeps track of the system, builds aggregate features in real-time, and monitors the model's predictive performance.

🌊 A River model is listening to Materialize for taxi departures. It makes a prediction each time a taxi departs. The prediction is then sent to Redpanda, and then gets picked up by Materialize.

🔮 The River model is also listening to Materialize for taxi arrivals. Each time a taxi arrives, Materialize joins the original features with the trip duration. This labelled sample is fed into the River model.

💾 The inference and learning parts coordinate each other by storing the model in a SQLite database.

💅🏻 Metabase is used to monitor the overall system in real-time -- actually, the dashboard is refreshed every 5 seconds, which is good enough.
