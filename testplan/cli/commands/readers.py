"""
Implements reader commands of the TPS command line tool.
"""
from glob import glob
from urllib.parse import urlparse, parse_qs
from typing import Callable, Type, List

import click
from boltons.iterutils import flatten

from testplan.cli.utils.actions import ParseSingleAction, ParseMultipleAction
from testplan.cli.utils.command_list import CommandList
from testplan.importers import ResultImporter
from testplan.importers.cppunit import CPPUnitResultImporter
from testplan.importers.gtest import GTestResultImporter
from testplan.importers.junit import JUnitResultImporter
from testplan.importers.testplan import TestplanResultImporter
from testplan.report import TestReport


single_reader_commands = CommandList()


def with_input(func: Callable) -> Callable:
    """
    Attaches a "source" argument to the command.
    """
    return click.argument(
        "source", type=click.Path(exists=True), required=True
    )(func)


def with_plan_options(func: Callable) -> Callable:
    """
    Attaches "name" and "description" options to the command.
    """
    options = [
        click.option(
            "-n",
            "--name",
            "name",
            type=str,
            help="The name of the generated testplan and test",
        ),
        click.option(
            "-d",
            "--description",
            "description",
            type=str,
            help="Description of the result",
        ),
    ]

    for option_decorator in options[::-1]:
        func = option_decorator(func)
    return func


class ReaderAction(ParseSingleAction):
    """
    Reader action class that implements a single report parser.
    """

    def __init__(
        self, importer: Type[ResultImporter], *args, **kwargs
    ) -> None:
        """
        :param importer: test result importer type
        """
        self.importer = importer(*args, **kwargs)

    def __call__(self) -> TestReport:
        return self.importer.import_result().as_test_report()


@single_reader_commands.command(name="fromcppunit")
@with_input
@with_plan_options
def from_cppunit(
    source: click.Path, name: str, description: str
) -> ReaderAction:
    """
    Reads a CppUnit XML result.

    :param source: path to source file
    :param name: name of the generated in-memory testplan
    :param description: description of generated test result
    """
    return ReaderAction(CPPUnitResultImporter, source, name, description)


@single_reader_commands.command(name="fromgtest")
@with_input
@with_plan_options
def from_gtest(
    source: click.Path, name: str, description: str
) -> ReaderAction:
    """
    Reads a GoogleTest XML result.

    :param source: path to source file
    :param name: name of the generated in-memory testplan
    :param description: description of generated test result
    """
    return ReaderAction(GTestResultImporter, source, name, description)


@single_reader_commands.command(name="fromjson")
@with_input
def from_json(source: click.Path) -> ReaderAction:
    """
    Reads a Testplan JSON result.

    :param source: path to source file
    """
    return ReaderAction(TestplanResultImporter, source)


@single_reader_commands.command(name="fromjunit")
@with_input
@with_plan_options
def from_junit(
    source: click.Path, name: str, description: str
) -> ReaderAction:
    """
    Reads a JUnit result.

    :param source: path to source file
    :param name: name of the generated in-memory testplan
    :param description: description of generated test result
    """
    return ReaderAction(JUnitResultImporter, source, name, description)


class ComposedParseAction(ParseMultipleAction):
    """
    Class for calling upon multiple reader action instances.
    """

    def __init__(self, actions: List[ReaderAction]) -> None:
        """
        :param actions: list of reader actions
        """
        self.actions = actions

    def __call__(self) -> List[TestReport]:
        return [action() for action in self.actions]


_IMPORTERS = {
    "json": TestplanResultImporter,
    "cppunit": CPPUnitResultImporter,
    "gtest": GTestResultImporter,
}


def get_actions_for_uri(uri: str) -> List[ReaderAction]:
    """
    Selects and instantiates actions for URI.

    :param uri: URI
    """
    importer = _IMPORTERS.get(uri.scheme)
    # TODO: Error handling

    files = glob(uri.path, recursive=True)
    importer_args = parse_qs(uri.query) if uri.query else {}

    return [ReaderAction(importer, file, **importer_args) for file in files]


multi_reader_commands = CommandList()


@multi_reader_commands.command(name="from")
@click.argument("uri_list")
def from_list(uri_list: str) -> ComposedParseAction:
    """
    Reads multiple input files in one go.

    It takes a list of comma separated URIs. The URI scheme should be a known
    format similar to from* commands, e.g. fromjson /tmp/a.json translates to
    json:/tmp/a.json. Globs can be used in the URIs like
    json:/tmp/report_*.json,cppunit:/tmp/result_*.xml

    :param uri_list: comma separated string of URIs
    """
    uris = [urlparse(uri) for uri in uri_list.split(",")]
    actions = flatten([get_actions_for_uri(uri) for uri in uris])

    return ComposedParseAction(actions)
