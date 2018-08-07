from schema import Schema, Use

from testplan.common.config import ConfigOption
from testplan.common.exporters import BaseExporter, ExporterConfig
from testplan.logger import TESTPLAN_LOGGER
from testplan.testing import tagging


class Exporter(BaseExporter):
    pass


class TagFilteredExporterConfig(ExporterConfig):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('report_tags', default=[],
                block_propagation=False): [Use(tagging.validate_tag_value)],
            ConfigOption('report_tags_all', default=[],
                block_propagation=False): [Use(tagging.validate_tag_value)]
        }


class TagFilteredExporter(Exporter):
    """
    This is a meta exporter that generates tag filtered clones
    of the original test report and calls `export` operation on a new
    instance of `exporter_class`.

    Basically multiple sub-export operations will be
    run for each generated clone report, however if the clone report
    is empty the export operation will be skipped.
    """
    ALL = 'all'
    ANY = 'any'

    CONFIG = TagFilteredExporterConfig
    exporter_class = None

    def get_params(self, tag_dict, filter_type):
        """
        Return the keyword parameters (as a dict) that will be used for
        `exporter_class` instance initialization. The keys and values
        should be valid arguments in line with `exporter_class`'s config.

        :param tag_dict: Tag context for the current sub-export operation.
        :type tag_dict: ``dict`` of ``set``
        :param filter_type: all / any
        :type filter_type: ``str``
        :return: dict of keyword arguments
        """
        return {}

    def get_exporter(self, **params):
        """
        Return a new instance of `exporter_class`,
        initialized with given `params`.

        :param params: Keyword arguments that will be
                       used for initializing `exporter_class`.
        :return: Instance of `exporter_class`
        """
        if not self.exporter_class:
            raise AttributeError('`exporter_class` not set.')

        exporter = self.exporter_class(**params)
        exporter.cfg.parent = self.cfg
        return exporter

    def get_filtered_source(self, source, tag_dict, filter_type):
        """
        Create a clone of the original report and
        filter it with the given filter type & tag context.

        Also populate cloned report's meta
        attribute with the tag label.

        :param source: Original test report.
        :type source: :py:class:`~testplan.report.testing.base.TestReport`
        :param tag_dict: Tag context for the current filtered test report.
        :type tag_dict: ``dict`` of ``set``
        :param filter_type: all / any
        :type filter_type: ``str``
        """
        tag_label = tagging.tag_label(tag_dict)
        result = source.filter_by_tags(
            tag_dict,
            all_tags=filter_type == self.ALL
        )
        result.meta['report_tags_{}'.format(filter_type)] = tag_label
        return result

    def get_skip_message(self, source, tag_dict, filter_type):
        """
        :param source: Cloned test report.
        :type source: :py:class:`~testplan.report.testing.base.TestReport`
        :param tag_dict: Tag context for the current filtered test report.
        :type tag_dict: ``dict`` of ``set``
        :param filter_type: all / any
        :type filter_type: ``str``
        :return: String message to be displayed on skipped export operations.
        :rtype: ``str``
        """
        return (
            'Empty report for tags: `{tag_label}`, filter_type:'
            ' `{filter_type}`, skipping export operation.'
        ).format(
            tag_label=tagging.tag_label(tag_dict),
            filter_type=filter_type
        )

    def export_clones(self, source, tag_dicts, filter_type):
        """
        Create clones of the original report using the given tag & filter
        context, initialize a new exporter for each clone and run the export
        operation, if the clone report is not empty.

        :param source: Original test report.
        :type source: :py:class:`~testplan.report.testing.base.TestReport`
        :param tag_dicts: List of tag dictionaries, a new export operation
                          will be run for each dict in the list.
        :type tag_dicts: ``list`` of ``dict``
        :param filter_type: all / any, will be used for tag filtering strategy.
        :type filter_type: ``str``
        :return: None
        """
        if filter_type not in [self.ALL, self.ANY]:
            raise ValueError('Invalid filter type: {}'.format(filter_type))

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
                        filter_type=filter_type
                    )
                )

    def export(self, source):
        """
        Run export operation for exact (all) and any matching tag groups.

        :param source: Test report.
        :type source: :py:class:`~testplan.report.testing.base.TestReport`
        :return: None
        """
        self.export_clones(
            source=source,
            tag_dicts=self.cfg.report_tags,
            filter_type=self.ANY)

        self.export_clones(
            source=source,
            tag_dicts=self.cfg.report_tags_all,
            filter_type=self.ALL)
