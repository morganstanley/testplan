import click


from testplan.cli.commands import single_reader_commands
from testplan.cli.commands import writer_commands
from testplan.cli.utils.actions import ProcessResultAction, ParseSingleAction


@click.group(name="convert", chain=True)
def convert():
    """
    Convert a single input file to testplan format.

    Once converted, then can dump to a target destination or display it through a local webui.
    The parameters forms a pipeline which starts with a source command (from*) then any write (to*)
    or a display command.

    use convert COMMAND --help to get more details of the subcommands.
    """
    pass


@convert.resultcallback()
def run_actions(actions):

    parse, *processors = actions

    if not (
        isinstance(parse, ParseSingleAction)
        and all((isinstance(p, ProcessResultAction) for p in processors))
    ):
        raise click.UsageError(
            "convert need a single parser like from* and can have many processor or targets like to* or display"
        )

    result = parse()

    for process in processors:
        result = process(result)


single_reader_commands.register_to(convert)
writer_commands.register_to(convert)
