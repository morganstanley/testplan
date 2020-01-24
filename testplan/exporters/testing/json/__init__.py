"""
    JSON exporter for test reports, relies on `testplan.report.testing.schemas`
    for `dict` serialization and JSON conversion.
"""
from __future__ import absolute_import

import os
import json

from testplan import defaults

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig

from testplan.report.testing.schemas import TestReportSchema


from ..base import Exporter, save_attachments


class JSONExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`JSONExporter <testplan.exporters.testing.json.JSONExporter>`
    object.
    """
    @classmethod
    def get_options(cls):
        return {
            ConfigOption('json_path'): str
        }


class JSONExporter(Exporter):
    """
    Json Exporter.

    :param json_path: File path for saving json report.
    :type json_path: ``str``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """
    CONFIG = JSONExporterConfig

    def export(self, source):

        json_path = self.cfg.json_path

        if len(source):
            test_plan_schema = TestReportSchema(strict=True)
            data = test_plan_schema.dump(source).data

            # Save the Testplan report.
            with open(json_path, 'w') as json_file:
                json.dump(data, json_file)

            # Save any attachments.
            attachments_dir = os.path.join(
                os.path.dirname(json_path),
                defaults.ATTACHMENTS
            )
            save_attachments(report=source, directory=attachments_dir)

            self.logger.exporter_info(
                'JSON generated at %s', os.path.abspath(json_path))
        else:
            self.logger.exporter_info(
                'Skipping JSON creation for empty report: %s', source.name)
