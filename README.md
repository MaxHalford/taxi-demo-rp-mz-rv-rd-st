# taxis-rp-mz-rv-mb

## Architecture

<div  align="center">
    <img width="70%" src="https://user-images.githubusercontent.com/8095957/187725375-b517706b-306d-42df-ba16-c6ae6214529a.png">
</div>

🐼 Redpanda acts as a message bus, storing all the data produced by the entire system.

🚕 An event is sent to Redpanda each time a taxi departs. Once the taxi arrives at its destination, the duration of the trip is also sent to Redpanda.

🍥 Materialize consumes the event and label topics from Redpanda to build features in real-time.

🌊 A River model is listening to Redpanda for taxi departures. It makes a prediction each time a taxi departs. It builds feature from the taxi event departure, and also queries Materialize to obtain real-time aggregate features.

🔮 The River model is also listening to Redpanda for taxi arrivals. Each time a taxi arrives, the trip duration is linked with the features that were used for the prediction, and the

💾

💅🏻 Metabase is used to monitor the overall system in real-time -- actually, the dashboards refreshes every 5 seconds, which is good enough.
