"""
HTTP exporter for uploading test reports via http transmission. The web server
must be able to handle POST request and receive data in JSON format.
"""

import json

import requests
from schema import Or, And, Use

from testplan.common.config import ConfigOption
from testplan.common.utils.validation import is_valid_url
from testplan.common.exporters import ExporterConfig
from testplan.report.testing.schemas import TestReportSchema

from ..base import Exporter


class CustomJsonEncoder(json.JSONEncoder):
    """To jsonify data that cannot be serialized by default JSONEncoder."""
    def default(self, obj):  # pylint: disable = method-hidden
        return str(obj)


class HTTPExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`HTTPExporter <testplan.exporters.testing.http.HTTPExporter>`
    object.
    """
    @classmethod
    def get_options(cls):
        return {
            ConfigOption('http_url'): is_valid_url,
            ConfigOption('timeout', default=60):
                Or(None, And(Use(int), lambda n: n > 0))
        }


class HTTPExporter(Exporter):
    """
    Json Exporter.

    :param http_url: Http url for posting data.
    :type http_url: ``str``
    :param timeout: Connection timeout.
    :type timeout: ``int``

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
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(
                    url=url, headers=headers,
                    data=json.dumps(data, cls=CustomJsonEncoder),
                    timeout=self.cfg.timeout)
                response.raise_for_status()
            except requests.exceptions.RequestException as exp:
                errmsg = 'Failed to export to {}: {}'.format(url, str(exp))
        else:
            errmsg = (
                'Skipping exporting test report via http '
                'for empty report: {}'.format(data['name']))

        return response, errmsg


    def export(self, source):

        http_url = self.cfg.http_url
        test_plan_schema = TestReportSchema(strict=True)
        data = test_plan_schema.dump(source).data
        _, errmsg = self._upload_report(http_url, data)

        if errmsg:
            self.logger.exporter_info(errmsg)
        else:
            self.logger.exporter_info('Test report posted to %s', http_url)
