"""
    JSON exporter for Test reports, relies on `testplan.report.testing.schemas`
    for `dict` serialization and JSON conversion.
"""
from __future__ import absolute_import

import os
import json

from schema import Or

from testplan import defaults
from testplan.common.utils.timing import wait
from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig
from testplan.report.testing.schemas import TestReportSchema
from testplan.web_ui.web_app import WebServer
from ..base import Exporter, save_attachments


class WebServerExporterConfig(ExporterConfig):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption(
                'ui_port', default=defaults.WEB_SERVER_PORT,
                block_propagation=False): Or(None, int),
            ConfigOption(
                'web_server_startup_timeout',
                default=defaults.WEB_SERVER_TIMEOUT): int,
        }


class WebServerExporter(Exporter):

    CONFIG = WebServerExporterConfig

    def export(self, source):
        if self.cfg.ui_port is None:
            raise ValueError('`ui_port` cannot be None.')
        if len(source):
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
            self._web_server_thread = WebServer(
                port=self.cfg.ui_port,
                data_path=data_path,
                report_name=report_name)

            self._web_server_thread.start()
            wait(self._web_server_thread.ready,
                 self.cfg.web_server_startup_timeout,
                 raise_on_timeout=True)

            (host, port) = self._web_server_thread.server.bind_addr

            self.url = 'http://{host}:{port}/testplan/local'.format(
                host=host,
                port=port)
            self.logger.exporter_info(
                'View the JSON report in the browser: {}'.format(self.url))
        else:
            self.logger.exporter_info(
                'Skipping starting web server'
                ' for empty report: {}'.format(source.name))
