"""
Stdout renderers for assertion/entry objects.

Unlike exporters, stdout renderers receive native entry objects, instead
of their serialized (dict) versions.
"""

import os
import re
import pprint
from typing import Any, Optional

from terminaltables import AsciiTable

from testplan.common.utils.registry import Registry
from .. import base

# Will be used for default conversion like: NotEqual -> Not Equal
ASSERTION_NAME_PATTERN = re.compile(r"([A-Z])")


class StdOutRegistry(Registry):
    def get_category(self, obj: Any) -> str:
        return obj.meta_type  # type: ignore[no-any-return]

    def indented_msg(self, msg: str, indent: int) -> str:
        parts = [indent * " " + line for line in msg.split(os.linesep)]
        return os.linesep.join(parts)

    def log_entry(self, entry: Any, stdout_style: Any) -> None:
        from testplan.testing.base import ASSERTION_INDENT

        logger = self[entry]()
        header = logger.get_header(entry)
        details = logger.get_details(entry) or ""
        output_style = stdout_style.get_style(passing=bool(entry))

        if header is None:
            raise ValueError(
                "Empty header returned by {logger} for {entry}".format(
                    logger=logger, entry=entry
                )
            )

        header_msg = self.indented_msg(header, ASSERTION_INDENT)
        details_msg = self.indented_msg(details, ASSERTION_INDENT + 2)

        if output_style.display_assertion:
            self.logger.user_info(header_msg)

        if details and output_style.display_assertion_detail:
            self.logger.user_info(details_msg)


registry = StdOutRegistry()


@registry.bind_default()
class BaseRenderer:
    """Absolute fallback for all entries."""

    def get_default_header(self, entry: Any) -> str:
        return ASSERTION_NAME_PATTERN.sub(
            " \\1", entry.__class__.__name__
        ).strip()

    def get_header_text(self, entry: Any) -> str:
        return entry.description or self.get_default_header(entry)

    def get_header(self, entry: Any) -> Optional[str]:
        return self.get_header_text(entry)

    def get_details(self, entry: Any) -> Optional[str]:
        pass


@registry.bind(base.Group)
class GroupRenderer:
    def get_header(self, entry: Any) -> str:
        return entry.description or "Group"


@registry.bind(base.Log)
class LogRenderer(BaseRenderer):
    def get_header(self, entry: Any) -> Optional[str]:
        if entry.description:
            return str(entry.description)
        elif isinstance(entry.message, str):
            return str(entry.message)
        else:
            return self.get_default_header(entry)

    def get_details(self, entry: Any) -> Optional[str]:
        if isinstance(entry.message, str):
            if entry.description:
                return str(entry.message)
            else:
                return None
        else:
            return pprint.pformat(entry.message)


@registry.bind(base.Attachment)
class AttachmentRenderer(BaseRenderer):
    def get_details(self, entry: Any) -> Optional[str]:
        return "Attach file: {}".format(entry.source_path)


@registry.bind(base.MatPlot)
class MatPlotRenderer(BaseRenderer):
    def get_details(self, entry: Any) -> Optional[str]:
        return "MatPlot graph generated at: {}".format(entry.source_path)


@registry.bind(base.Plotly)
class PlotlyRenderer(BaseRenderer):
    def get_details(self, entry: Any) -> Optional[str]:
        return "Plotly graph generated at: {}".format(entry.source_path)


@registry.bind(base.Directory)
class DirectoryRenderer(BaseRenderer):
    def get_details(self, entry: Any) -> Optional[str]:
        return "Attach directory: {}".format(entry.source_path)


@registry.bind(base.TableLog)
class TableLogRenderer(BaseRenderer):
    def get_details(self, entry: base.TableLog) -> str:
        """
        This method converts the entire input table into a string using AsciiTable.

        :param entry: the TableLog object we want to convert
        :return: rows of the input table joined into a single string with newline characters
        """
        # AsciiTable doesn't support cells with 'bytes' values so first we need to convert them to 'str'
        for j, row in enumerate(entry.table):
            for i, cell in enumerate(row):
                if isinstance(cell, bytes):
                    entry.table[j][i] = str(cell)

        return AsciiTable([entry.columns, *entry.table]).table  # type: ignore[no-any-return]


@registry.bind(base.DictLog, base.FixLog)
class DictLogRenderer(BaseRenderer):
    def get_details(self, entry: Any) -> Optional[str]:
        result = []
        if len(entry.flattened_dict) == 0:
            result.append("(empty)")

        for row in entry.flattened_dict:
            offset, key, val = row
            result.append(
                "{}{}    {}".format(
                    " " * 4 * offset,
                    "Key({}),".format(key) if key else "",
                    "{} <{}>".format(val[1], val[0])
                    if isinstance(val, (tuple, list))
                    else "",
                )
            )

        if result:
            result.append("")

        return str(os.linesep.join(result))
