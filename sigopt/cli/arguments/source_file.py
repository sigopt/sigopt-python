import click


def file_contents(ctx, param, value):
  if value is None:
    return None
  with open(value, "r") as fp:
    return fp.read()

source_file_option = click.option(
  '-s',
  '--source-file',
  type=click.Path(exists=True),
  callback=file_contents,
)
