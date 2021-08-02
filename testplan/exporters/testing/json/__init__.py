"""
JSON exporter for test reports, relies on `testplan.report.testing.schemas`
for `dict` serialization and JSON conversion.
"""

import os
import json
import copy
import pathlib
import hashlib

from testplan import defaults

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig

from testplan.report import ReportCategories
from testplan.report.testing.schemas import TestReportSchema

from ..base import Exporter, save_attachments


def gen_attached_report_names(json_path):
    """
    Generate file names of structure JSON report and assertions JSON report.
    """
    basename, _ = os.path.splitext(os.path.basename(json_path))
    digest = hashlib.md5(
        os.path.realpath(json_path).encode("utf-8")
    ).hexdigest()

    return (
        "{}-structure-{}.json".format(basename, digest),
        "{}-assertions-{}.json".format(basename, digest),
    )


class JSONExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`JSONExporter <testplan.exporters.testing.json.JSONExporter>`
    object.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("json_path"): str,
            # By default a single JSON file should be exported, with cfg option
            # `split_json_report` enabled it generates a main JSON file with 2
            # attachments, this is useful when there's some limit on file size.
            ConfigOption("split_json_report", default=False): bool,
        }


class JSONExporter(Exporter):
    """
    Json Exporter.

    :param json_path: File path for saving json report.
    :type json_path: ``str``
    :param split_json_report: Split a single json report into several parts.
    :type split_json_report: ``bool``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = JSONExporterConfig

    def __init__(self, name="JSON exporter", **options):
        super(JSONExporter, self).__init__(**options)

    def export(self, source):

        json_path = pathlib.Path(self.cfg.json_path).resolve()

        if len(source):
            json_path.parent.mkdir(parents=True, exist_ok=True)

            test_plan_schema = TestReportSchema(strict=True)
            data = test_plan_schema.dump(source).data
            attachments_dir = json_path.parent / defaults.ATTACHMENTS

            # Save the Testplan report.
            if self.cfg.split_json_report:
                (
                    structure_filename,
                    assertions_filename,
                ) = gen_attached_report_names(json_path)
                structure_filepath = attachments_dir / structure_filename
                assertions_filepath = attachments_dir / assertions_filename

                meta, structure, assertions = self.split_json_report(data)
                attachments_dir.mkdir(parents=True, exist_ok=True)

                with open(structure_filepath, "w") as json_file:
                    json.dump(structure, json_file)
                with open(assertions_filepath, "w") as json_file:
                    json.dump(assertions, json_file)

                save_attachments(report=source, directory=attachments_dir)
                meta["version"] = 2
                # Modify dict ref may change the original `TestReport` object
                meta["attachments"] = copy.deepcopy(meta["attachments"])
                meta["attachments"][structure_filename] = str(
                    structure_filepath
                )
                meta["attachments"][assertions_filename] = str(
                    assertions_filepath
                )
                meta["structure_file"] = structure_filename
                meta["assertions_file"] = assertions_filename

                with open(json_path, "w") as json_file:
                    json.dump(meta, json_file)
            else:
                save_attachments(report=source, directory=attachments_dir)
                data["version"] = 1

                with open(json_path, "w") as json_file:
                    json.dump(data, json_file)

            self.logger.exporter_info("JSON generated at %s", json_path)
            return self.cfg.json_path
        else:
            self.logger.exporter_info(
                "Skipping JSON creation for empty report: %s", source.name
            )
            return None

    @staticmethod
    def split_json_report(data):
        """Split a single Json into several parts."""

        def split_assertions(entries, assertions):
            """Remove assertions from report and place them in a dictionary."""
            for entry in entries:
                if entry.get("category") == ReportCategories.TESTCASE:
                    assertions[entry["uid"]] = entry["entries"]
                    entry["entries"] = []
                elif "entries" in entry:
                    split_assertions(entry["entries"], assertions)

        meta, structure, assertions = data, data["entries"], {}
        meta["entries"] = []
        split_assertions(structure, assertions)
        return meta, structure, assertions

    @staticmethod
    def merge_json_report(meta, structure, assertions, strict=True):
        """Merge parts of json report into a single one."""

        def merge_assertions(entries, assertions, strict=True):
            """Fill assertions into report by the unique id."""
            for entry in entries:
                if entry.get("category") == ReportCategories.TESTCASE:
                    if entry["uid"] in assertions:
                        entry["entries"] = assertions[entry["uid"]]
                    elif strict:
                        raise RuntimeError(
                            "Testcase report uid missing: {}".format(
                                entry["uid"]
                            )
                        )
                elif "entries" in entry:
                    merge_assertions(entry["entries"], assertions, strict)

        merge_assertions(structure, assertions, strict)
        meta["entries"] = structure
        return meta
