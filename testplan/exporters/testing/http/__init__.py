"""
HTTP exporter for uploading test reports via HTTP transmission. The web server
must be able to handle POST request and receive data in JSON format.
"""

import json
from typing import Any, Tuple, Union, Optional, Dict

import requests
from schema import Or, And, Use

from testplan.common.config import ConfigOption
from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    verify_export_context,
)
from testplan.common.utils.validation import is_valid_url
from testplan.report import TestReport
from testplan.report.testing.schemas import TestReportSchema
from ..base import Exporter


class CustomJsonEncoder(json.JSONEncoder):
    """To jsonify data that cannot be serialized by default JSONEncoder."""

    def default(self, obj: Any) -> str:  # pylint: disable = method-hidden
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
            ConfigOption("http_url"): is_valid_url,
            ConfigOption("timeout", default=60): Or(
                None, And(Use(int), lambda n: n > 0)
            ),
        }


class HTTPExporter(Exporter):
    """
    HTTP exporter.

    :param http_url: Http url for posting data.
    :type http_url: ``str``
    :param timeout: Connection timeout.
    :type timeout: ``int``

    Inherits all :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = HTTPExporterConfig

    def __init__(self, name: str = "HTTP exporter", **options):
        super(HTTPExporter, self).__init__(name=name, **options)

    def _upload_report(
        self, url: str, data: Any
    ) -> Tuple[Union[None, requests.Request], str]:
        """
        Upload Json data, then return the response from server with an
        error message (if any).

        :param url:
        :param data:
        :return: response, even if None, and error message pair
        :raises HTTPError: thrown if response results in HTTP error
        """
        response = None
        errmsg = ""

        if data:
            headers = {"Content-Type": "application/json"}
            try:
                response = requests.post(
                    url=url,
                    headers=headers,
                    data=json.dumps(data, cls=CustomJsonEncoder),
                    timeout=self.cfg.timeout,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as exp:
                errmsg = "Failed to export to {}: {}".format(url, str(exp))
        else:
            errmsg = (
                "Skipping exporting test report via http for"
                " empty report: {}".format(data.get("name") or "[UNKNOWN]")
            )

        return response, errmsg

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> Optional[Dict]:
        """
        Uploads report to remote HTTP server.

        :param: source: Testplan report to export
        :param: export_context: information about other exporters
        :return: dictionary containing the possible output
        """

        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        http_url = self.cfg.http_url
        test_plan_schema = TestReportSchema()
        data = test_plan_schema.dump(source)
        result = None
        _, errmsg = self._upload_report(http_url, data)

        if errmsg:
            self.logger.error(errmsg)
        else:
            self.logger.user_info("Test report posted to %s", http_url)
            result = {"http_url": http_url}
        return result
