"""
HTTP exporter for uploading test reports via http transmission. The web server
must be able to handle POST request and receive data in JSON format.
"""
import re
import json

import requests
from schema import Or, Regex

from testplan.common.config import ConfigOption
from testplan.common.utils.validation import is_valid_url
from testplan.common.exporters import ExporterConfig
from testplan.report.testing.schemas import TestReportSchema

from ..base import Exporter


class HTTPExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`HTTPExporter <testplan.exporters.testing.http.HTTPExporter>`
    object.
    """
    @classmethod
    def get_options(cls):
        return {
            ConfigOption('url'): is_valid_url
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

    def _upload_report(self, url, data):
        """
        Upload Json data, then return the response from server with an
        error message (if any).
        """
        response = None
        errmsg = ''

        if data and data['entries']:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            try:
                response = requests.post(
                    url=url, data=json.dumps(data), headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as exp:
                errmsg = 'Failed to export to {}: {}'.format(url, exp)
        else:
            errmsg = (
                'Skipping exporting test report via http '
                'for empty report: %s', data.name)

        return response, errmsg

    def export(self, source):

        url = self.cfg.url
        test_plan_schema = TestReportSchema(strict=True)
        data = test_plan_schema.dump(source).data
        _, errmsg = self._upload_report(url, data)

        if errmsg:
            self.logger.exporter_info(errmsg)
        else:
            self.logger.exporter_info('Test report posted to %s', url)
