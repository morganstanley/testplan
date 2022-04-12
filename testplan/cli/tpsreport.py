"""
Entry point for TPS command line tool.
"""
import click

from testplan.cli.converter import convert
from testplan.cli.display import display
from testplan.cli.merger import merge


@click.group()
def cli() -> None:
    """
    (T)est(P)lan (S)uper (REPORT)

    A Testplan tool for report manipulation.
    """
    pass


cli.add_command(convert)
cli.add_command(merge)
cli.add_command(display)


if __name__ == "__main__":
    cli()
