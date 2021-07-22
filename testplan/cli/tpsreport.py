import click

from testplan.cli.converter import convert
from testplan.cli.merger import merge


@click.group()
def cli():
    pass


cli.add_command(convert)
cli.add_command(merge)


if __name__ == "__main__":
    cli()
