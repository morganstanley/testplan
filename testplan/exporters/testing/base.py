""" TODO """
"""
Implements base exporter objects.
"""
import pathlib
from typing import Dict, List, Optional
from shutil import copyfile

from schema import Use

from testplan.common.config import ConfigOption
from testplan.common.exporters import BaseExporter, ExporterConfig
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.path import makedirs
from testplan.report.testing.base import TestReport
from testplan.testing import tagging
from testplan.defaults import ATTACHMENTS


# TODO: what we mean here? This is just another dot on the inheritance graph.
class Exporter(BaseExporter):
    """TODO"""

    pass


class TagFilteredExporterConfig(ExporterConfig):
    """
    Configuration object for :py:class:`~TagFilteredExporter`.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("report_tags"): [Use(tagging.validate_tag_value)],
            ConfigOption("report_tags_all"): [Use(tagging.validate_tag_value)],
        }


class TagFilteredExporter(Exporter):
    """
    This is a meta exporter that generates tag filtered clones
    of the original test report and calls `export` operation on a new
    instance of an `Exporter` class.

    This is achieved, by running multiple sub-export operations for each clone.
    However, if the clone report is empty, the export operation is skipped.
    """

    ALL: str = "all"
    ANY: str = "any"

    CONFIG: TagFilteredExporterConfig = TagFilteredExporterConfig
    exporter_class: BaseExporter = None

    def get_params(self, tag_dict: Dict, filter_type: str) -> Dict:
        """
        Return the keyword parameters (as a dict) that will be used for
        `exporter_class` instance initialization. The keys and values
        should be valid arguments in line with `exporter_class`'s config.

        :param tag_dict: tag context for the current sub-export operation
        :param filter_type: all / any
        :return: dictionary of keyword arguments
        """
        return {}

    def get_exporter(self, **params) -> BaseExporter:
        """
        Instantiates `exporter_class` with given `params`.

        :param params: keyword arguments used for initializing `exporter_class`
        :return: instance of `exporter_class`
        :raises AttributeError: if there is no exporter class set
        """
        # TODO: shouldn't this be a TypeError for non-BaseExporter instance?
        if not self.exporter_class:
            raise AttributeError("`exporter_class` not set.")

        # pylint: disable=not-callable
        exporter = self.exporter_class(**params)
        # pylint: enable=not-callable

        exporter.cfg.parent = self.cfg
        return exporter

    def get_filtered_source(
        self,
        source: TestReport,
        tag_dict: Dict,
        filter_type: str,
    ) -> TestReport:
        """
        Creates a filtered clone of the report by filter type and tag context.

        :param source: Testplan report
        :param tag_dict: tag context for filtering
        :param filter_type: all / any
        :return: filtered clone
        """
        tag_label = tagging.tag_label(tag_dict)
        result = source.filter_by_tags(
            tag_dict, all_tags=filter_type == self.ALL
        )
        result.meta["report_tags_{}".format(filter_type)] = tag_label
        return result

    def get_skip_message(
        self,
        source: Optional[TestReport],
        tag_dict: Dict,
        filter_type: str,
    ) -> str:
        """
        Produces message logged if filtered clone is empty.

        :param source: cloned test report
        :param tag_dict: tag context for the current filtered test report
        :param filter_type: all / any
        :return: string message to be displayed on skipped export operations
        """
        return (
            "Empty report for tags: `{tag_label}`, filter_type:"
            " `{filter_type}`, skipping export operation."
        ).format(
            tag_label=tagging.tag_label(tag_dict), filter_type=filter_type
        )

    def export_clones(
        self,
        source: TestReport,
        tag_dicts: List[Dict],
        filter_type: str,
    ) -> None:
        """
        Creates clones of the report using the given tag & filter
        context, initialize a new exporter for each clone and run the export
        operation, if the clone report is not empty.

        :param source: Testplan report
        :param tag_dicts: list of tag dictionaries, export is run for each item
        :param filter_type: all / any
        """
        if filter_type not in [self.ALL, self.ANY]:
            raise ValueError("Invalid filter type: {}".format(filter_type))

        for tag_dict in tag_dicts:
            clone = self.get_filtered_source(source, tag_dict, filter_type)

            if clone is not None:
                params = self.get_params(tag_dict, filter_type)
                exporter = self.get_exporter(**params)
                exporter.export(clone)
            else:
                TESTPLAN_LOGGER.exporter_info(
                    self.get_skip_message(
                        source=clone,
                        tag_dict=tag_dict,
                        filter_type=filter_type,
                    )
                )

    def export(self, source: TestReport) -> None:
        """
        Runs the export operation for exact (all) and any matching tag groups.

        :param source: Testplan report to export
        """
        self.export_clones(
            source=source, tag_dicts=self.cfg.report_tags, filter_type=self.ANY
        )

        self.export_clones(
            source=source,
            tag_dicts=self.cfg.report_tags_all,
            filter_type=self.ALL,
        )


def save_attachments(report: TestReport, directory: str) -> Dict[str, str]:
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
                    raise FileNotFoundError(
                        f'Attachment "{dst}" not found in either {dirname} or'
                        f' the nearest "{ATTACHMENTS}" directory of test report'
                    )
            copyfile(src=src, dst=dst_path)
            moved_attachments[dst] = str(dst_path)

    return moved_attachments
