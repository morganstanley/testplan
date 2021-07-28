from glob import glob
from urllib.parse import urlparse, parse_qs
from boltons.iterutils import flatten

import click


from testplan.cli.utils.actions import ParseSingleAction, ParseMultipleAction
from testplan.cli.utils.command_list import CommandList
from testplan.importers.cppunit import CPPUnitResultImporter
from testplan.importers.gtest import GTestResultImporter
from testplan.importers.testplan import TestplanResultImporter
from testplan.report import TestReport

single_reader_commands = CommandList()


def with_input(fn):
    return click.argument(
        "source", type=click.Path(exists=True), required=True
    )(fn)


def with_plan_options(fn):
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
        fn = option_decorator(fn)
    return fn


class ReaderAction(ParseSingleAction):
    def __init__(self, importer, *args, **kwargs):
        self.importer = importer(*args, **kwargs)

    def __call__(self) -> TestReport:
        return self.importer.import_result().as_test_report()


@single_reader_commands.command(name="fromcppunit")
@with_input
@with_plan_options
def from_cppunit(source, name, description):
    return ReaderAction(CPPUnitResultImporter, source, name, description)


@single_reader_commands.command(name="fromgtest")
@with_input
@with_plan_options
def from_gtest(source, name, description):
    return ReaderAction(GTestResultImporter, source, name, description)


@single_reader_commands.command(name="fromjson")
@with_input
def from_json(source):
    return ReaderAction(TestplanResultImporter, source)


class ComposedParseAction(ParseMultipleAction):
    def __init__(self, actions):
        self.actions = actions

    def __call__(self):
        return [action() for action in self.actions]


_IMPORTERS = {
    "json": TestplanResultImporter,
    "cppunit": CPPUnitResultImporter,
    "gtest": GTestResultImporter,
}


def get_actions_for_uri(uri):
    importer = _IMPORTERS.get(uri.scheme)
    # TODO: Error handling

    files = glob(uri.path, recursive=True)
    importer_args = parse_qs(uri.query) if uri.query else {}

    return [ReaderAction(importer, file, **importer_args) for file in files]


multi_reader_commands = CommandList()


@multi_reader_commands.command(name="from")
@click.argument("uri_list")
def from_list(uri_list: str) -> ParseMultipleAction:
    uris = [urlparse(uri) for uri in uri_list.split(",")]
    actions = flatten([get_actions_for_uri(uri) for uri in uris])

    return ComposedParseAction(actions)
