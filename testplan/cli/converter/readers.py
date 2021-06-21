import click

from testplan.cli.utils.command_list import CommandList
from testplan.importers.cppunit import CPPUnitResultImporter
from testplan.importers.gtest import GTestResultImporter

reader_commands = CommandList()


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


@reader_commands.command(name="fromcppunit")
@with_input
@with_plan_options
def from_cppunit(source, name, description):
    def parse(result):
        importer = CPPUnitResultImporter(source, name, description)
        return importer.import_result().as_test_report()

    return parse


@reader_commands.command(name="fromgtest")
@with_input
@with_plan_options
def from_gtest(source, name, description):
    def parse(result):
        importer = GTestResultImporter(source, name, description)
        return importer.import_result().as_test_report()

    return parse
