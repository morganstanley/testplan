"""
HTTP exporter for uploading test reports via http transmission. The web server
must be able to handle POST request and receive data in JSON format.
"""
import re
import json

import requests
from schema import Or, Regex

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig
from testplan.report.testing.schemas import TestReportSchema

from ..base import Exporter


class HTTPExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`HTTPExporter <testplan.exporters.testing.json.HTTPExporter>`
    object.
    """
    @classmethod
    def get_options(cls):
        return {
            ConfigOption('url'):
                Regex(r'^http[s]?://[\w\d_-]+(:\d{2,5})?.+$', flags=re.I)
        }


class HTTPExporter(Exporter):
    """
    Json Exporter.

    :param url: Http url for posting data.
    :type url: ``str``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """
    CONFIG = HTTPExporterConfig

    def __init__(self, **options):
        super(HTTPExporter, self).__init__(**options)

    def export(self, source):

        url = self.cfg.url

        if len(source):
            test_plan_schema = TestReportSchema(strict=True)
            data = test_plan_schema.dump(source).data
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            try:
                response = requests.post(
                    url=url, data=json.dumps(data), headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as exp:
                self.logger.exporter_info(
                    'Failed to export to {}: {}'.format(url, exp))
            else:
                self.logger.exporter_info(
                    'Test report posted to {}'.format(url))
        else:
            self.logger.exporter_info(
                'Skipping exporting test report via http'
                ' for empty report: {}'.format(source.name))
