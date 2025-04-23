"""
JSON exporter for test reports, relies on `testplan.report.testing.schemas`
for `dict` serialization and JSON conversion.
"""

import hashlib
import os
import pathlib

from shutil import copyfile
from typing import Dict, Optional

from testplan.common.config import ConfigOption
from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    verify_export_context,
)
from testplan.common.utils.json import json_dumps, json_loads
from testplan.common.utils.path import makedirs
from testplan.defaults import ATTACHMENTS, RESOURCE_DATA
from testplan.report.testing.base import TestReport, TestCaseReport
from testplan.report.testing.schemas import TestReportSchema
from ..base import Exporter


def save_resource_data(
    report: TestReport, directory: pathlib.Path
) -> pathlib.Path:
    directory.mkdir(parents=True, exist_ok=True)
    with open(report.resource_meta_path) as meta_file:
        meta_info = json_loads(meta_file.read())
    for host_meta in meta_info["entries"]:
        if "resource_file" in host_meta:
            dist_path = (
                directory / pathlib.Path(host_meta["resource_file"]).name
            )
            copyfile(src=host_meta["resource_file"], dst=dist_path)
            host_meta["resource_file"] = dist_path.name
    meta_path = directory / pathlib.Path(report.resource_meta_path).name
    with open(meta_path, "w") as meta_file:
        meta_file.write(json_dumps(meta_info))
    return meta_path


def gen_attached_report_names(json_path):
    """
    Generate file names of structure JSON report and assertions JSON report.
    """
    basename, _ = os.path.splitext(os.path.basename(json_path))
    digest = hashlib.md5(
        os.path.normcase(os.path.realpath(json_path)).encode("utf-8")
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
        super(JSONExporter, self).__init__(name=name, **options)

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> Optional[Dict]:
        """
        Exports report to JSON files in the given directory.

        :param: source: Testplan report to export
        :param: export_context: information about other exporters
        :return: dictionary containing the possible output
        """

        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        result = None
        json_path = pathlib.Path(self.cfg.json_path).resolve()

        if not source.is_empty():
            json_path.parent.mkdir(parents=True, exist_ok=True)

            test_plan_schema = TestReportSchema()
            data = test_plan_schema.dump(source)
            attachments_dir = json_path.parent / ATTACHMENTS

            # Save resource monitor data
            if source.resource_meta_path:
                resource_dir = json_path.parent / RESOURCE_DATA
                save_resource_data(source, resource_dir)
                self.logger.user_info(
                    "Resource monitor data has been saved in %s", resource_dir
                )
                data["resource_meta_path"] = "local"
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
                    json_file.write(json_dumps(structure))
                with open(assertions_filepath, "w") as json_file:
                    json_file.write(json_dumps(assertions))

                meta["attachments"] = self.save_attachments(
                    report=source,
                    directory=attachments_dir,
                )
                meta["version"] = 2
                meta["attachments"][structure_filename] = str(
                    structure_filepath
                )
                meta["attachments"][assertions_filename] = str(
                    assertions_filepath
                )
                meta["structure_file"] = structure_filename
                meta["assertions_file"] = assertions_filename

                with open(json_path, "w") as json_file:
                    json_file.write(json_dumps(meta))
            else:
                data["attachments"] = self.save_attachments(
                    report=source,
                    directory=attachments_dir,
                )
                data["version"] = 1

                with open(json_path, "w") as json_file:
                    json_file.write(json_dumps(data))

            self.logger.user_info("JSON generated at %s", json_path)
            result = {"json": self.cfg.json_path}
        else:
            self.logger.user_info(
                "Skipping JSON creation for empty report: %s", source.name
            )
        return result

    def save_attachments(
        self, report: TestReport, directory: str
    ) -> Dict[str, str]:
        """
        Saves the report attachments to the given directory.

        :param report: Testplan report.
        :param directory: directory to save attachments in
        :return: dictionary of destination paths
        """
        moved_attachments = {}
        attachments = getattr(report, "attachments", None)
        if attachments:
            for dst, src in attachments.items():
                src = pathlib.Path(src)
                dst_path = pathlib.Path(directory) / dst
                makedirs(dst_path.parent)
                if not src.is_file():
                    dirname = src.parent
                    # Try retrieving the file from "_attachments" directory that is
                    # near to the test report, the downloaded report might be moved
                    src = pathlib.Path.cwd() / ATTACHMENTS / dst
                    if not src.is_file():
                        self.logger.warning(
                            'Attachment "%s" not found in either %s or the nearest "%s" directory of test report',
                            dst,
                            dirname,
                            ATTACHMENTS,
                        )
                        continue
                copyfile(src=src, dst=dst_path)
                moved_attachments[dst] = str(dst_path)

        return moved_attachments

    @staticmethod
    def split_json_report(data):
        """Split a single Json into several parts."""

        def split_assertions(entries, assertions):
            """Remove assertions from report and place them in a dictionary."""
            for entry in entries:
                if entry["type"] == TestCaseReport.__name__:
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
                if entry["type"] == TestCaseReport.__name__:
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
