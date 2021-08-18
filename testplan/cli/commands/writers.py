import click

from testplan.cli.utils.actions import ProcessResultAction
from testplan.cli.utils.command_list import CommandList
from testplan.exporters.testing import JSONExporter, WebServerExporter
from testplan.report import TestReport

writer_commands = CommandList()


class ToJsonAction(ProcessResultAction):
    def __init__(self, output: str):
        self.output = output

    def __call__(self, result: TestReport) -> TestReport:
        exporter = JSONExporter(json_path=self.output)
        exporter.export(result)

        return result


@writer_commands.command(name="tojson")
@click.argument("output", type=click.Path())
def to_json(output):
    """
    write a Testplan json result
    """

    return ToJsonAction(output=output)


class DisplayAction(ProcessResultAction):
    def __init__(self, port: int):
        self.port = port

    def __call__(self, result: TestReport) -> TestReport:

        exporter = WebServerExporter(ui_port=self.port)
        exporter.export(result)
        exporter.wait_for_kb_interrupt()

        return result


@writer_commands.command(name="display")
@click.option(
    "--port",
    "-p",
    type=int,
    default=0,
    help="the local port the webserver is using",
)
def display(port):
    """
    serve the result through a local webui.
    """
    return DisplayAction(port)
