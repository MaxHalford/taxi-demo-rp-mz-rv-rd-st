# Simulation service

This will:

1. Create `pick_ups` and `drop_off` Redpanda topics
2. Upload some River model to Redis
3. Loop through River's [taxi trips dataset](https://riverml.xyz/0.11.1/api/datasets/Taxis/)
4. Send the events in the order they actually happened to Redpanda
