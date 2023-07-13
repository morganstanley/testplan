"""
Web server exporter for test reports, it opens a local http web server
which can display the test result.
"""
from typing import Dict, Optional

from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    verify_export_context,
    run_exporter,
)
from testplan.report.testing.base import TestReport
from testplan.web_ui.server import WebUIServer
from ..base import Exporter
from ..json import JSONExporter


class WebServerExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`WebServerExporter <testplan.exporters.testing.webserver.WebServerExporter>`  # pylint: disable=line-too-long
    object.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("ui_port", default=defaults.WEB_SERVER_PORT): int,
            ConfigOption("json_path", default=defaults.JSON_PATH): str,
            ConfigOption(
                "web_server_startup_timeout",
                default=defaults.WEB_SERVER_TIMEOUT,
            ): int,
        }


class WebServerExporter(Exporter):
    """
    Web Server Exporter.

    :param ui_port: Port of web application.
    :type ui_port: ``int``
    :param json_path: File path for saving JSON report.
    :type json_path: ``str``
    :param web_server_startup_timeout: Timeout for starting web server.
    :type web_server_startup_timeout: ``int``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = WebServerExporterConfig

    def __init__(self, name="Web Server exporter", **options):
        super(WebServerExporter, self).__init__(name=name, **options)
        self._server = None

    @property
    def report_url(self):
        if self._server:
            return self._server.report_url
        return None

    @property
    def web_server_thread(self):
        if self._server:
            return self._server.web_server_thread
        return None

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> Optional[Dict]:
        """
        Exports report to JSON then opens a local webserver to display it.

        :param: source: Testplan report to export
        :param: export_context: information about other exporters
        :return: dictionary containing the possible output
        """

        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        result = None
        if len(source):
            exporter = JSONExporter(
                json_path=self.cfg.json_path, split_json_report=False
            )
            run_exporter(
                exporter=exporter, source=source, export_context=export_context
            )

            self._server = WebUIServer(
                json_path=self.cfg.json_path,
                ui_port=self.cfg.ui_port,
                web_server_startup_timeout=self.cfg.web_server_startup_timeout,
            )
            self._server.display()

            result = {"port": self.cfg.ui_port}
        else:
            self.logger.user_info(
                "Skipping starting web server for empty report: %s",
                source.name,
            )
        return result
