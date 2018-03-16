"""
    Stdout renderers for assertion/entry objects.

    Unlike exporters, stdout renderers receive native entry objects, instead
    of their serialized (dict) versions.
"""

import os
import re

from terminaltables import AsciiTable

from testplan.common.utils.registry import Registry
from testplan.logger import TESTPLAN_LOGGER
from .. import base

# Will be used for default conversion like: NotEqual -> Not Equal
ASSERTION_NAME_PATTERN = re.compile(r"([A-Z])")


class StdOutRegistry(Registry):

    def get_category(self, obj):
        return obj.meta_type

    def indented_msg(self, msg, indent):
        parts = [
            indent * ' ' + line
            for line in msg.split(os.linesep)]
        return os.linesep.join(parts)

    def log_entry(self, entry, stdout_style):
        from testplan.testing.multitest.base import ASSERTION_INDENT
        logger = self[entry]()
        header = logger.get_header(entry)
        details = logger.get_details(entry) or ''
        output_style = stdout_style.get_style(passing=bool(entry))

        if not header:
            raise ValueError(
                'Empty header returned by'
                ' {logger} for {entry}'.format(
                    logger=logger,
                    entry=entry
                )
            )

        header_msg = self.indented_msg(header, ASSERTION_INDENT)
        details_msg = self.indented_msg(details, ASSERTION_INDENT + 2)

        if output_style.display_assertion:
            TESTPLAN_LOGGER.test_info(header_msg)

        if details and output_style.display_assertion_detail:
            TESTPLAN_LOGGER.test_info(details_msg)


registry = StdOutRegistry()


@registry.bind_default()
class BaseRenderer(object):
    """Absolute fallback for all entries."""

    def get_default_header(self, entry):
        return ASSERTION_NAME_PATTERN.sub(
            ' \\1', entry.__class__.__name__).strip()

    def get_header_text(self, entry):
        return entry.description or self.get_default_header(entry)

    def get_header(self, entry):
        return str(entry)

    def get_details(self, entry):
        pass


@registry.bind(base.Group)
class GroupRenderer(object):

    def get_header(self, entry):
        return entry.description or 'Group'


@registry.bind(base.TableLog)
class TableLogRenderer(BaseRenderer):

    def get_header(self, entry):
        return self.get_header_text(entry)

    def get_details(self, entry):
        rows = [[x for _, x in row.items()] for row in entry.table]
        return AsciiTable([entry.columns] + rows).table


@registry.bind(base.MatPlot)
class MatPlotRenderer(BaseRenderer):

    def get_header(self, entry):
        return self.get_header_text(entry)

    def get_details(self, entry):
        return 'MatPlot graph generated at: {}'.format(entry.image_file_path)
