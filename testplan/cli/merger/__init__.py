from builtins import isinstance
from itertools import takewhile, dropwhile
from typing import Union, List

import click

from testplan.cli.converter import writer_commands, reader_commands
from testplan.cli.utils.actions import (
    ParseSingleAction,
    ParseMultipleAction,
)
from testplan.report import TestReport


@click.group(name="merge", chain=True)
def merge():
    pass


def run_parse_action(parse: Union[ParseSingleAction, ParseMultipleAction], results: List[TestReport]):

    if isinstance(parse, ParseSingleAction):
        results.append(parse())
    elif isinstance(parse, ParseMultipleAction):
        results.extend(parse())


def is_parse_action(action):
    return isinstance(action, (ParseSingleAction, ParseMultipleAction))


@merge.resultcallback()
def run_actions(actions):

    # phase1 read inputs

    results = []

    for action in takewhile(is_parse_action, actions):
        run_parse_action(action, results)

    # phase2 merged
    merged_result = None
    # phase3 outputs/postprocessing
    for process in dropwhile(is_parse_action, actions):
        merged_result = process(merged_result)


@merge.command(name="from")
def from_list():
    pass


writer_commands.register_to(merge)
reader_commands.register_to(merge)
