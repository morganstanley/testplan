"""
    JSON exporter for Test reports, relies on `testplan.report.testing.schemas`
    for `dict` serialization and JSON conversion.
"""
from __future__ import absolute_import

import json

from schema import Schema

from testplan import defaults
from testplan.logger import TESTPLAN_LOGGER

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig

from testplan.report.testing.schemas import TestReportSchema


from ..base import Exporter


MAX_FILENAME_LENGTH = 100


class JSONExporterConfig(ExporterConfig):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption(
                'json_path', default=defaults.JSON_PATH,
                block_propagation=False): str
        }


class JSONExporter(Exporter):

    CONFIG = JSONExporterConfig

    def export(self, source):

        if self.cfg.json_path is None:
            raise ValueError('`json_path` cannot be None.')

        if len(source):
            test_plan_schema = TestReportSchema(strict=True)
            data = test_plan_schema.dump(source).data

            with open(self.cfg.json_path, 'w') as json_file:
                json.dump(data, json_file)

            TESTPLAN_LOGGER.exporter_info(
                'JSON generated at {}'.format(self.cfg.json_path))
        else:
            TESTPLAN_LOGGER.exporter_info(
                'Skipping JSON creation'
                ' for empty report: {}'.format(source.name))
