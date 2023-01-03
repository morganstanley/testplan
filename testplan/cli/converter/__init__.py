from typing import Sequence, Union

import click

from testplan.cli.commands import single_reader_commands
from testplan.cli.commands import writer_commands
from testplan.cli.utils.actions import ProcessResultAction, ParseSingleAction


@click.group(name="convert", chain=True)
def convert() -> None:
    """
    Parses provided result format and, optionally, writes to another/displays.
    """
    pass


@convert.result_callback()
def run_actions(
    actions: Sequence[Union[ParseSingleAction, ProcessResultAction]]
) -> None:
    """
    Result callback for `convert` command.

    :param actions: sequence of a single parser and, possibly, multiple
        processor actions.
    """
    parse, *processors = actions

    if not (
        isinstance(parse, ParseSingleAction)
        and all((isinstance(p, ProcessResultAction) for p in processors))
    ):
        raise click.UsageError(
            "convert needs a single parser of the form `from*` and can have"
            " multiple processors or targets of the form `to*` or `display`"
        )

    result = parse()

    for process in processors:
        result = process(result)


single_reader_commands.register_to(convert)
writer_commands.register_to(convert)
