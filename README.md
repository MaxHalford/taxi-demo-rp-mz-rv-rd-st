# taxis-rp-mz-rv-mb

## Architecture

![architecture](https://user-images.githubusercontent.com/8095957/187721317-59c5b2e3-2414-45b8-a8d4-985e13f0c25a.png)

🐼 Redpanda acts as a message bus, storing all the data produced by the entire system.

🚕 An event is sent to Redpanda each time a taxi departs. Once the taxi arrives at its destination, the duration of the trip is also sent to Redpanda.

🍥 Materialize consumes the event and label topics from Redpanda to build features in real-time.

🌊 A River model is used to predict the duration of a trip. The model is listening
