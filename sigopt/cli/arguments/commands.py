import click


commands_argument = click.argument('commands', nargs=-1, type=click.UNPROCESSED)
