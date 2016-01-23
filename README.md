# SigOpt Python API

This is the SigOpt Python API client.
Use this to natively call SigOpt API endpoints to create experiments and report data.

For the complete API documentation, visit [https://sigopt.com/docs](https://sigopt.com/docs).

Take a look in `examples` for example usage.

## Getting Started

Install the sigopt python modules with `pip install sigopt-python`.

Sign up for an account at [https://sigopt.com](https://sigopt.com).
In order to use the API, you'll need your `client_token` from your [user profile](https://sigopt.com/user/profile).

To call the API, instantiate a connection with your token.

```python
import sigopt.interface
conn = sigopt.interface.Connection(client_token=client_token)
```
Then, you can use the connection to issue API requests. An example creating an experiment and running the
optimization loop:

```python
experiment = conn.experiments().create(
  name='New Experiment',
  parameters=[{ 'name': 'param1', 'type': 'double', 'bounds': { 'min': 0, 'max': 1.0 }}],
)

suggestion = conn.experiments(experiment.id).suggestions().create()
value = evaluate_metric(suggestion) # Implement this, the return  value should be a number
conn.experiments(experiment.id).observations().create(
  'suggestion': suggestion.id,
  'value': value,
)
```

## Authentication

Your `client_token` does not have permission to view or modify information about individual user accounts,
so it is safe to include when running SigOpt in production.

## Endpoints

Endpoints are grouped by objects on the `Connection`.
For example, endpoints that interact with experiments are under `conn.experiments`.
`ENDPOINT_GROUP(ID)` operates on a single object, while `ENDPOINT_GROUP()` will operate on multiple objects.

`POST`, `GET`, `PUT` and `DELETE` translate to the method calls `create`, `fetch`, `update` and `delete`.
To retrieve an experiment, call `conn.experiments(ID).fetch()`. To create an experiment call 
`conn.experiments(ID).create()`. Parameters are passed to the API as named arguments.

Just like in the resource urls, `suggestions` and `observations` are under `experiments`.
Access these objects with `conn.experiments(ID).suggestions` and `conn.experiments(ID).observations`.
The REST endpoint `POST /v1/experiments/1/suggestions` then translates to `conn.experiments(ID).suggestions().create()`.

## Testing

To run the included tests, you'll need to install pytest (with `pip install pytest`). Then, just run

```bash
PYTHONPATH=. python -m pytest -rw -v test
```

![Build Status](https://travis-ci.org/sigopt/sigopt-python.svg?branch=master)
