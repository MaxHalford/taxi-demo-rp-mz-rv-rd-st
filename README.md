# taxis-rp-mz-rv-mb

## Architecture

<div  align="center">
    <img width="70%" src="https://user-images.githubusercontent.com/8095957/187721317-59c5b2e3-2414-45b8-a8d4-985e13f0c25a.png">
</div>

🐼 Redpanda acts as a message bus, storing all the data produced by the entire system.

🚕 An event is sent to Redpanda each time a taxi departs. Once the taxi arrives at its destination, the duration of the trip is also sent to Redpanda.

🍥 Materialize consumes the event and label topics from Redpanda and does stream processing on top. For instance, it build aggregate features in real-time which can fed into an machine learning model.

🌊 A River model is listening to Materialize for taxi departures. It makes a prediction each time a taxi departs.

🔮 The River model is also listening to Materialize for taxi arrivals. Each time a taxi arrives, the trip duration is joined with the features were used for the prediction -- thanks to Materialize -- and the pair is fed into the model so it can learn.

💾

💅🏻 Metabase is used to monitor the overall system in real-time -- actually, the dashboards refreshes every 5 seconds, which is good enough.
