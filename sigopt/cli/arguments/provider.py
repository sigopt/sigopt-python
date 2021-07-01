import click

from sigopt.orchestrate.provider.constants import STRING_TO_PROVIDER


provider_option = click.option(
  "--provider",
  type=click.Choice(sorted(STRING_TO_PROVIDER.keys())),
  required=True,
  help="The cloud provider. Use `custom` for your own cluster.",
)
