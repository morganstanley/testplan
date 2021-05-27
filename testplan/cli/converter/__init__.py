import click

from testplan.cli.converter.readers import reader_commands
from testplan.cli.converter.writers import writer_commands


@click.group(name="convert", chain=True)
def convert():
    pass


@convert.resultcallback()
def run_actions(actions):
    result = None
    for action in actions:
        result = action(result)


reader_commands.register_to(convert)
writer_commands.register_to(convert)
