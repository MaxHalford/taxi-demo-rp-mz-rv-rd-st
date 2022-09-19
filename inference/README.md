# Inference service

This will:

1. Create some Materialize views which consume the `pick_ups` and `drop_offs` RedPanda topics
2. Enrich each trip with features
3. Produce a prediction for each model and each trip
4. Send the predictions to Redpanda in a `predictions` topic
