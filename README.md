# SigOpt Python API

This is the SigOpt Python API client.
Use this to natively call SigOpt API endpoints to create experiments and report data.

For the complete API documentation, visit [https://sigopt.com/docs](https://sigopt.com/docs).

Take a look in `examples` for example usage.

## Getting Started

Install the sigopt python modules with `pip install sigopt-python`.

Sign up for an account at [https://sigopt.com](https://sigopt.com).
In order to use the API, you'll need your `user_token`, `client_token`, and `client_id` from [https://sigopt.com/user/profile](https://sigopt.com/user/profile).

To call the API, instantiate a connection with your tokens.

```python
import sigopt.interface
conn = sigopt.interface.Connection(user_token=user_token, client_token=client_token)
```
Then, you can use the connection to issue API requests. Some example requests:

```python
experiment = conn.experiments.create(client_id=client_id, data={
    'name': 'New Experiment',
  'parameters': [{ 'name': 'param1', 'type': 'double', 'bounds': { 'min': 0, 'max': 1.0 }}],
}).experiment

suggestion = conn.experiments(experiment.id).suggest().suggestion

conn.experiments(experiment.id).report(data={
  'assignments': suggestion.assignments,
  'value': 1.0,
})
```

## Authentication

When creating a `Connection`, you can specify either `user_token`, `client_token`, or both.
The API client will use the correct token for each API call.
However, if one of the tokens is missing, you will not be able to call endpoints that require that token.
We recommend only providing `client_token` when running SigOpt in production,
so that individual user credentials are not shared between members of the same organization.

## Endpoints

Endpoints are grouped by name on `Connection` objects.
For example, endpoints that interact with experiments are under `conn.experiments`.

Endpoints that operate on a single instance are called in the form `conn.ENDPOINT_GROUP(ID).ENDPOINT`.
For example, `conn.experiments(1).suggest()` will call the `suggest` endpoint on the experiment with ID 1.
This corresponds to the REST endpoint `/experiments/1/suggest.`

To retrieve an object, call `conn.ENDPOINT_GROUP(ID).fetch()`.
For example, `conn.experiments(1).fetch()` will fetch experiment 1.

To create an object, call `conn.ENDPOINT_GROUP.create()`. `conn.experiments.create()` will create an experiment.
