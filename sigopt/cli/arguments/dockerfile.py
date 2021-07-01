import click


dockerfile_option = click.option(
  "-d",
  "--dockerfile",
  type=click.Path(exists=True),
  default="./Dockerfile",
)
