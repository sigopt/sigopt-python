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
experiment = conn.experiment_create(client_id, data={
  'name': 'New Experiment',
  'parameters': [{ 'name': 'param1', 'type': 'double', 'bounds': { 'min': 0, 'max': 1.0 }}],
}).experiment

suggestion = conn.experiment_suggest(experiment.id).suggestion

conn.experiment_report(experiment.id, {
  'assignments': suggestion.assignments,
  'value': 1.0,
})
```
