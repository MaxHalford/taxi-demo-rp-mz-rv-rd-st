This will:

1. Create necessary Redpanda topics
2. Upload a River model to Redis
3. Loop through River's [taxi trips dataset](https://riverml.xyz/0.11.1/api/datasets/Taxis/)
4. Send the events in arrival order to Redpanda
