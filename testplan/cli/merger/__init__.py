from itertools import takewhile, dropwhile
from typing import Union, List

import click

from testplan.cli.commands import reader_commands
from testplan.cli.commands import writer_commands
from testplan.cli.merger.mergers import SimpleCombiner
from testplan.cli.utils.actions import (
    ParseSingleAction,
    ParseMultipleAction,
    ProcessResultAction,
)
from testplan.report import TestReport


@click.group(name="merge", chain=True)
def merge() -> None:
    """
    Merges many report files into a single Testplan.

    Currently a simple combine strategy is available which put all tests from the sources next to each other in
    the merged report. The subcommands forms a pipeline, which should start with source commands (from*) defining
    the inputs, then any write (to*) or a display command.

    The inpust can be any supported format they will be converted to Testplan format before the merge

    use merge COMMAND --help to get more details of the subcommands.
    """
    pass


def run_parse_action(
    parse: Union[ParseSingleAction, ParseMultipleAction],
    results: List[TestReport],
) -> None:
    """ """
    if isinstance(parse, ParseSingleAction):
        results.append(parse())
    elif isinstance(parse, ParseMultipleAction):
        results.extend(parse())


def is_parse_action(action: object) -> bool:
    """ """
    return isinstance(action, (ParseSingleAction, ParseMultipleAction))


@merge.result_callback()
def run_actions(actions) -> None:
    """ """
    # phase1 read inputs

    results = []

    parse_actions = list(takewhile(is_parse_action, actions))
    process_actions = list(dropwhile(is_parse_action, actions))

    if not parse_actions:
        raise click.UsageError("No inputs specified.")

    if not all(
        (isinstance(action, ProcessResultAction) for action in process_actions)
    ):
        raise click.UsageError(
            "after inputs only processors like to* or display are allowed"
        )

    for action in parse_actions:
        run_parse_action(action, results)

    # phase2 merge
    merged_result = SimpleCombiner().merge(results)
    # phase3 outputs/postprocessing
    for process in process_actions:
        merged_result = process(merged_result)


writer_commands.register_to(merge)
reader_commands.register_to(merge)
