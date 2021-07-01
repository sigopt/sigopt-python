import click

from ...config import config as _config
from .base import sigopt_cli


LOG_COLLECTION_PROMPT = '''Log Collection
\tThis will capture and upload the standard output and standard error of your
\tRuns so that you can view them on the SigOpt dashboard.
Enable log collection'''

CODE_TRACKING_PROMPT = '''Code Tracking
\tThis will record and upload the content of your code so that you can view it
\ton the SigOpt dashboard.
\tThe source code hash from your VCS (ie. Git) will be recorded even if this
\toption is disabled.
Enable code tracking'''

@sigopt_cli.command()
@click.option('--api-token', prompt='SigOpt API token (find at https://app.sigopt.com/tokens/info)')
@click.option(
  '--enable-log-collection/--no-enable-log-collection',
  prompt=LOG_COLLECTION_PROMPT,
)
@click.option(
  '--enable-code-tracking/--no-enable-code-tracking',
  prompt=CODE_TRACKING_PROMPT,
)
def config(api_token, enable_log_collection, enable_code_tracking):
  '''Configure the SigOpt client.'''
  _config.persist_configuration_options({
    _config.API_TOKEN_KEY: api_token,
    _config.CODE_TRACKING_ENABLED_KEY: enable_code_tracking,
    _config.LOG_COLLECTION_ENABLED_KEY: enable_log_collection,
  })
