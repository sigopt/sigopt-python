import click

from ...config import config as _config
from .base import sigopt_cli

API_TOKEN_PROMPT = 'SigOpt API token (find at https://app.sigopt.com/tokens/info)'

LOG_COLLECTION_PROMPT = '''Log Collection
\tThis will capture and upload the standard output and standard error of your
\tRuns from the CLI and notebook cells so that you can view them on the SigOpt dashboard.
Enable log collection'''

CELL_TRACKING_PROMPT = '''Notebook Cell Tracking
\tThis will record and upload the content of your notebook cells so that you can view them
\ton the SigOpt dashboard.
Enable cell tracking'''

@sigopt_cli.command()
@click.option('--api-token', prompt=API_TOKEN_PROMPT)
@click.option(
  '--enable-log-collection/--no-enable-log-collection',
  prompt=LOG_COLLECTION_PROMPT,
)
@click.option(
  '--enable-cell-tracking/--no-enable-cell-tracking',
  prompt=CELL_TRACKING_PROMPT,
)
def config(api_token, enable_log_collection, enable_cell_tracking):
  '''Configure the SigOpt client.'''
  _config.persist_configuration_options({
    _config.API_TOKEN_KEY: api_token,
    _config.CELL_TRACKING_ENABLED_KEY: enable_cell_tracking,
    _config.LOG_COLLECTION_ENABLED_KEY: enable_log_collection,
  })
