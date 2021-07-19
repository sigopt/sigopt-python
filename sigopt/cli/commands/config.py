import click

from ...config import config as _config
from .base import sigopt_cli


LOG_COLLECTION_PROMPT = '''Log Collection
\tThis will capture and upload the standard output and standard error of your
\tRuns so that you can view them on the SigOpt dashboard.
Enable log collection'''

@sigopt_cli.command()
@click.option('--api-token', prompt='SigOpt API token (find at https://app.sigopt.com/tokens/info)')
@click.option(
  '--enable-log-collection/--no-enable-log-collection',
  prompt=LOG_COLLECTION_PROMPT,
)
def config(api_token, enable_log_collection):
  '''Configure the SigOpt client.'''
  _config.persist_configuration_options({
    _config.API_TOKEN_KEY: api_token,
    _config.LOG_COLLECTION_ENABLED_KEY: enable_log_collection,
  })
