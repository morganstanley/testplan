import click

from testplan.cli.converter import convert
from testplan.cli.display import display
from testplan.cli.merger import merge


@click.group()
def cli():
    """
    (T)est(P)lan (S)uper (REPORT)

    A Testplan Tool for report manipulation
    """
    pass


cli.add_command(convert)
cli.add_command(merge)
cli.add_command(display)


if __name__ == "__main__":
    cli()
