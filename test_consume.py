import kafka

consumer = kafka.KafkaConsumer(
    "departures", bootstrap_servers=["localhost:9092"], auto_offset_reset="earliest"
)
for message in consumer:
    print(message)
