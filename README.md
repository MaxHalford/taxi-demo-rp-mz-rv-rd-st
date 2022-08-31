# taxis-rp-mz-rv-mb

## Architecture

![architecture](https://user-images.githubusercontent.com/8095957/187684728-de06c7ac-481c-457c-9fe5-4c03c6d762e9.png)

🐼 Redpanda acts as a message bus, storing all the events produced by the overall system.

🚕 An event is sent to Redpanda each time a taxi departs. Once the taxi arrives at its destination, the duration of the trip is also sent to Redpanda.
