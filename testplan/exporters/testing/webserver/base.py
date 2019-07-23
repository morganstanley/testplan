"""
    JSON exporter for Test reports, relies on `testplan.report.testing.schemas`
    for `dict` serialization and JSON conversion.
"""
from __future__ import absolute_import

import ipaddress
import os
import json

from schema import Or

from testplan import defaults
from testplan.common.utils.timing import wait
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
            ConfigOption(
                'ui_port', default=defaults.WEB_SERVER_PORT): int,
            ConfigOption(
                'web_server_startup_timeout',
                default=defaults.WEB_SERVER_TIMEOUT): int,
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

    def export(self, source):
        """Serve the web UI locally for our test report."""
        if self.cfg.ui_port is None:
            raise ValueError('`ui_port` cannot be None.')

        if not len(source):
            self.logger.exporter_info(
                'Skipping starting web server'
                ' for empty report: {}'.format(source.name))
            return

        if not self._ui_installed:
            self.logger.warning(
                'Cannot display web UI for report locally since the Testplan '
                'UI is not installed.\n'
                'Install the UI by running `install-testplan-ui`')
            return

        test_plan_schema = TestReportSchema(strict=True)
        data = test_plan_schema.dump(source).data

        # Save the Testplan report as a JSON.
        with open(defaults.JSON_PATH, 'w') as json_file:
            json.dump(data, json_file)

        # Save any attachments.
        data_path = os.path.dirname(defaults.JSON_PATH)
        report_name = os.path.basename(defaults.JSON_PATH)
        attachments_dir = os.path.join(data_path, defaults.ATTACHMENTS)
        save_attachments(report=source, directory=attachments_dir)

        self.logger.exporter_info(
            'JSON generated at {}'.format(defaults.JSON_PATH))

        # Start the web server.
        self._web_server_thread = web_app.WebServer(
            port=self.cfg.ui_port,
            data_path=data_path,
            report_name=report_name)

        self._web_server_thread.start()
        wait(self._web_server_thread.ready,
             self.cfg.web_server_startup_timeout,
             raise_on_timeout=True)

        (host, port) = self._web_server_thread.server.bind_addr

        # Check for an IPv6 address. Web browsers require IPv6 addresses to be
        # enclosed in [].
        try:
            if ipaddress.ip_address(host).version == 6:
                host = '[{}]'.format(host)
        except ValueError:
            # Expected if the host is a host name instead of an IP address.
            pass

        self.url = 'http://{host}:{port}/testplan/local'.format(
            host=host,
            port=port)
        self.logger.exporter_info(
            'View the JSON report in the browser: {}'.format(self.url))

    @property
    def _ui_installed(self):
        """
        Check if the UI is installed. Just check that the build/ dir exists
        at the expected path.
        """
        build_path = os.path.join(
            web_app.TESTPLAN_UI_STATIC_DIR, 'testing', 'build')
        return os.path.isdir(build_path)
