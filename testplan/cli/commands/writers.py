import click

from testplan.cli.utils.actions import ProcessResultAction
from testplan.cli.utils.command_list import CommandList
from testplan.exporters.testing import JSONExporter, WebServerExporter, PDFExporter
from testplan.report import TestReport
from testplan.report.testing.styles import StyleArg


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


class ToPDFAction(ProcessResultAction):
    def __init__(self, filename: str, style: StyleArg):
        self.filename = filename
        self.style = style

    def __call__(self, result: TestReport) -> TestReport:
        exporter = PDFExporter(pdf_path=self.filename, pdf_style=self.style.value)
        exporter.create_pdf(result)
        print(f"PDF written to {self.filename}")
        return result


@writer_commands.command(name="topdf")
@click.option('-f', '--filename', required=True, type=click.Path())
@click.option('--detailed', default=False, type=bool)
def to_pdf(filename, detailed):
    """
    write a Testplan pdf result
    """
    if detailed:
        return ToPDFAction(filename=filename, style=StyleArg.DETAILED)

    return ToPDFAction(filename=filename, style=StyleArg.SUMMARY)


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
