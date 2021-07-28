import click

from testplan.cli.commands import single_reader_commands
from testplan.cli.commands import writer_commands


@click.group(name="convert", chain=True)
def convert():
    pass


@convert.resultcallback()
def run_actions(actions):

    parse, *processors = actions
    # TODO: validate the action chain should be a single parser and processors

    result = parse()

    for process in processors:
        result = process(result)


single_reader_commands.register_to(convert)
writer_commands.register_to(convert)
