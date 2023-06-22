"""
Implements writer commands of the TPS command line tool.
"""
import os
import tempfile

import click

from testplan.cli.utils.actions import ProcessResultAction
from testplan.cli.utils.command_list import CommandList
from testplan.common.exporters import ExportContext
from testplan.common.utils import logger
from testplan.exporters.testing import JSONExporter, PDFExporter, XMLExporter
from testplan.report import TestReport
from testplan.report.testing.styles import StyleArg
from testplan.web_ui.server import WebUIServer


writer_commands = CommandList()


class ToJsonAction(ProcessResultAction):
    """
    Writer action for exporting JSON format.
    """

    def __init__(self, output: str) -> None:
        """
        :param output: path to write output to
        """
        self.output = output

    def __call__(self, result: TestReport) -> TestReport:
        """
        :param result: Testplan report to export
        """
        exporter = JSONExporter(json_path=self.output)
        export_context = ExportContext()
        exporter.export(source=result, export_context=export_context)

        return result


@writer_commands.command(name="tojson")
@click.argument("output", type=click.Path())
def to_json(output: click.Path) -> ToJsonAction:
    """
    Writer command for exporting JSON format.

    :param output: path to write output to
    """
    return ToJsonAction(output=output)


class ToPDFAction(ProcessResultAction, logger.Loggable):
    """
    Writer action for exporting PDF format.
    """

    def __init__(self, filename: str, style: StyleArg) -> None:
        """
        :param filename: filename to write to
        :param style: report style to use
        """
        logger.Loggable.__init__(self)  # Enable logging via self.logger
        self.filename = filename
        self.style = style

    def __call__(self, result: TestReport) -> TestReport:
        """
        :param result: Testplan report to export
        """
        exporter = PDFExporter(
            pdf_path=self.filename, pdf_style=self.style.value
        )
        exporter.create_pdf(result)
        self.logger.user_info("PDF written to %s", self.filename)
        return result


@writer_commands.command(name="topdf")
@click.argument("filename", required=True, type=click.Path())
@click.option(
    "--pdf-style",
    default="summary",
    type=click.Choice(
        ["result", "summary", "extended", "detailed"], case_sensitive=False
    ),
    help="""result - only the result of the run will be shown\n
            summary - test details will be shown\n
            extended - passing tests will include testcase detail,\
             while failing tests will include assertion detail\n
            detailed - passing tests will include assertion detail,\
             while failing tests will include assertion detail\n
        """,
)
def to_pdf(filename: click.Path, pdf_style: click.Choice) -> ToPDFAction:
    """
    Writer command for exporting PDF format.

    :param filename: filename to write to
    :param pdf_style: report style to use
    """
    if pdf_style == "result":
        return ToPDFAction(filename=filename, style=StyleArg.RESULT_ONLY)
    elif pdf_style == "summary":
        return ToPDFAction(filename=filename, style=StyleArg.SUMMARY)
    elif pdf_style == "extended":
        return ToPDFAction(filename=filename, style=StyleArg.EXTENDED_SUMMARY)
    elif pdf_style == "detailed":
        return ToPDFAction(filename=filename, style=StyleArg.DETAILED)


class ToJUnitAction(ProcessResultAction, logger.Loggable):
    """
    Writer action for exporting JUnit XML format.
    """

    def __init__(self, dir_name: str) -> None:
        """
        :param dir_name: directory to write XML files to
        """
        logger.Loggable.__init__(self)
        self.dir_name = dir_name

    def __call__(self, result: TestReport) -> TestReport:
        exporter = XMLExporter(xml_dir=self.dir_name)
        export_context = ExportContext()
        exporter.export(source=result, export_context=export_context)
        self.logger.user_info("XML files written to %s", self.dir_name)
        return result


@writer_commands.command(name="tojunit")
@click.argument("dir_name", required=True, type=click.Path())
def to_junit(dir_name: click.Path) -> ToJUnitAction:
    """
    Writer command for exporting JUnit format.

    :param dir_name: directory to write XML files to
    :return: JUnit writer action to perform
    """
    return ToJUnitAction(dir_name=dir_name)


class DisplayAction(ProcessResultAction):
    """
    Display action for serving result through a local web UI.
    """

    def __init__(self, port: int = 0) -> None:
        """
        :param port: port number to use
        """
        self.port = port

    def __call__(self, result: TestReport) -> TestReport:
        # TPR handles commands with a pipeline, resulting in calls like
        #   - tpr convert fromjson $JSON_FILE display
        #   - tpr convert fromdb $DOC_ID display
        # reading data from input and transform it into `TestReport`, then
        # the output of actual command becomes input of the next (display).
        # A `WebUIServer` is used to save the data into a temporary single JSON
        # which will be displayed it in browser. If the original input file is
        # a single JSON, this process might be optimized. But here, we stick to
        # the pipeline concept to make implementation consistent.
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "report.json")
            exporter = JSONExporter(
                json_path=json_path, split_json_report=False
            )
            export_context = ExportContext()
            exporter.export(source=result, export_context=export_context)

            ui_server = WebUIServer(json_path=json_path, ui_port=self.port)
            ui_server.display()
            ui_server.wait_for_kb_interrupt()

        return result


@writer_commands.command(name="display")
@click.option(
    "--port",
    "-p",
    type=int,
    default=0,
    help="the local port the webserver is using",
)
def display(port: int = 0) -> DisplayAction:
    """
    Serves the result through a local web UI.

    :param port: port number to use
    """
    return DisplayAction(port)
