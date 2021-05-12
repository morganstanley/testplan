"""
Web server exporter for test reports, it opens a local http web server
which can display the test result.
"""

import os
import json

from testplan import defaults
from testplan.common.utils.timing import wait
from testplan.common.utils import networking
from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig
from testplan.report.testing.schemas import TestReportSchema
from testplan.web_ui import web_app
from ..base import Exporter, save_attachments


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
    :param web_server_startup_timeout: Timeout for starting web server.
    :type web_server_startup_timeout: ``int``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = WebServerExporterConfig

    def __init__(self, **options):
        super(WebServerExporter, self).__init__(**options)
        self._report_url = None

    @property
    def report_url(self):
        return self._report_url

    def export(self, source):
        """Serve the web UI locally for our test report."""
        if not len(source):
            self.logger.exporter_info(
                "Skipping starting web server for " "empty report: %s",
                source.name,
            )
            return

        if not self._ui_installed:
            self.logger.warning(
                "Cannot display web UI for report locally since the Testplan "
                "UI is not installed.\n"
                "Install the UI by running `install-testplan-ui`"
            )
            return

        test_plan_schema = TestReportSchema(strict=True)
        data = test_plan_schema.dump(source).data

        # Save the Testplan report as a JSON.
        with open(defaults.JSON_PATH, "w") as json_file:
            json.dump(data, json_file)

        # Save any attachments.
        data_path = os.path.dirname(defaults.JSON_PATH)
        attachments_dir = os.path.join(data_path, defaults.ATTACHMENTS)
        save_attachments(report=source, directory=attachments_dir)

        self.logger.exporter_info("JSON generated at %s", defaults.JSON_PATH)

        self.display(defaults.JSON_PATH)
        return defaults.JSON_PATH

    def display(self, json_path):
        """Display a generated JSON in the web UI"""
        # Start the web server.

        data_path = os.path.dirname(json_path)
        report_name = os.path.basename(json_path)

        self._web_server_thread = web_app.WebServer(
            port=self.cfg.ui_port, data_path=data_path, report_name=report_name
        )

        self._web_server_thread.start()
        wait(
            self._web_server_thread.ready,
            self.cfg.web_server_startup_timeout,
            raise_on_timeout=True,
        )

        (host, port) = self._web_server_thread.server.bind_addr
        self._report_url = "http://localhost:{}/testplan/local".format(port)

        self.logger.exporter_info(
            "View the JSON report in the browser:\n%s",
            networking.format_access_urls(host, port, "/testplan/local"),
        )

    @property
    def _ui_installed(self):
        """
        Check if the UI is installed. Just check that the build/ dir exists
        at the expected path.
        """
        build_path = os.path.join(
            web_app.TESTPLAN_UI_STATIC_DIR, "testing", "build"
        )
        return os.path.isdir(build_path)
