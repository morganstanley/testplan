"""
Base classes go here.
"""
import datetime
import operator
import pprint
import re
import os

from past.builtins import basestring

from testplan.common.utils.convert import nested_groups
from testplan.common.utils.timing import utcnow
from testplan.common.utils.table import TableEntry
from testplan.common.utils.reporting import fmt
from testplan.common.utils.convert import flatten_formatted_object
from testplan.common.utils import path as path_utils
from testplan import defaults


__all__ = ["BaseEntry", "Group", "Summary", "Log"]


# Will be used for default conversion like: NotEqual -> Not Equal
ENTRY_NAME_PATTERN = re.compile(r"([A-Z])")

DEFAULT_CATEGORY = "DEFAULT"
DEFAULT_FLAG = "DEFAULT"


def readable_name(class_name):
    """NotEqual -> Not Equal"""
    return ENTRY_NAME_PATTERN.sub(" \\1", class_name).strip()


def get_table(source, keep_column_order=True):
    """
    Return table formatted as a TableEntry.

    :param source: Tabular data.
    :type source: ``list`` of ``list`` or ``list`` of ``dict``
    :param keep_column_order: Flag whether column order should be maintained.
    :type keep_column_order: ``bool``
    :return: Formatted table.
    :rtype: ``list`` of ``dict``
    """
    if not source:
        return []

    table = source if isinstance(source, TableEntry) else TableEntry(source)
    return table.as_list_of_dict(keep_column_order=keep_column_order)


class BaseEntry(object):
    """Base class for all entries, stores common context like time etc."""

    meta_type = "entry"

    def __init__(self, description, category=None, flag=None):
        self.utc_time = utcnow()
        self.machine_time = datetime.datetime.now()
        self.description = description
        self.category = category or DEFAULT_CATEGORY
        self.flag = flag or DEFAULT_FLAG

        # Will be set explicitly via containers
        self.line_no = None
        self.file_path = None

    def __str__(self):
        return repr(self)

    def __bool__(self):
        return True

    @property
    def name(self):
        """MyClass -> My Class"""
        return readable_name(self.__class__.__name__)

    __nonzero__ = __bool__

    def serialize(self):
        """Shortcut method for serialization via schemas"""
        from .schemas.base import registry

        return registry.serialize(self)


class Group(object):

    # we treat Groups as assertions so we can render them with pass/fail context
    meta_type = "assertion"

    def __init__(self, entries, description=None):
        self.description = description
        self.entries = entries

    def __bool__(self):
        return self.passed

    __nonzero__ = __bool__

    def __repr__(self):
        return "{}(entries={}, description='{}')".format(
            self.__class__.__name__, self.entries, self.description
        )

    @property
    def passed(self):
        """
        Empty groups are truthy AKA does not
        contain anything that is failing.
        """
        return (not self.entries) or all([bool(e) for e in self.entries])


class Summary(Group):
    """
    A meta assertion that stores a subset of given entries.
    Groups assertion data into a nested structure by category, assertion type
    and pass/fail status.

    If any of the entries is a Group, then its entries are expanded and
    the Group object is discarded.
    """

    def __init__(
        self,
        entries,
        description=None,
        num_passing=defaults.SUMMARY_NUM_PASSING,
        num_failing=defaults.SUMMARY_NUM_FAILING,
        key_combs_limit=defaults.SUMMARY_KEY_COMB_LIMIT,
    ):
        self.num_passing = num_passing
        self.num_failing = num_failing
        self.key_combs_limit = key_combs_limit

        super(Summary, self).__init__(
            entries=self._summarize(
                entries,
                num_passing=num_passing,
                num_failing=num_failing,
                key_combs_limit=key_combs_limit,
            ),
            description=description,
        )

    def _flatten(self, entries):
        """
        Recursively traverse entries and expand entries of groups.
        """

        def _flatten(items):
            result = []
            for item in items:
                if isinstance(item, Group) and not isinstance(item, Summary):
                    result.extend(_flatten(item.entries))
                else:
                    result.append(item)
            return result

        return _flatten(entries)

    def _summarize(self, entries, num_passing, num_failing, key_combs_limit):
        # Circular imports
        from .assertions import Assertion
        from .summarization import registry

        # Get rid of Groups (but leave summaries)
        entries = self._flatten(entries)
        summaries = [e for e in entries if isinstance(e, Summary)]

        # Create nested data of depth 3
        # Group by category, class name and pass/fail status
        groups = nested_groups(
            iterable=(e for e in entries if isinstance(e, Assertion)),
            key_funcs=[
                operator.attrgetter("category"),
                lambda obj: obj.__class__.__name__,
                operator.truth,
            ],
        )

        result = []
        limits = dict(
            num_passing=num_passing,
            num_failing=num_failing,
            key_combs_limit=key_combs_limit,
        )

        for category, category_grouping in groups:
            cat_group = Group(
                entries=[], description="Category: {}".format(category)
            )
            for class_name, assertion_grouping in category_grouping:
                asr_group = Group(
                    entries=[],
                    description="Assertion type: {}".format(
                        readable_name(class_name)
                    ),
                )
                for pass_status, assertion_entries in assertion_grouping:
                    # Apply custom grouping, otherwise just trim the
                    # list of entries via default summarization func.
                    summarizer = registry[class_name]
                    summary_group = summarizer(
                        category=category,
                        class_name=class_name,
                        passed=pass_status,
                        entries=assertion_entries,
                        limits=limits,
                    )
                    if len(summary_group.entries):
                        asr_group.entries.append(summary_group)
                cat_group.entries.append(asr_group)
            result.append(cat_group)
        return summaries + result


class Log(BaseEntry):
    """Log a str to the report."""

    def __init__(self, message, description=None, flag=None):
        if isinstance(message, basestring):
            self.message = message
        else:
            self.message = pprint.pformat(message)

        if not description:
            description = next((l for l in self.message.split("\n") if l), "")
            if len(description) > 80:
                description = description[0:80] + "..."

        super(Log, self).__init__(description=description, flag=flag)


class TableLog(BaseEntry):
    """Log a table to the report."""

    def __init__(self, table, display_index=False, description=None):
        self.table = get_table(table)
        self.indices = range(len(self.table))
        self.display_index = display_index
        self.columns = self.table[0].keys()

        super(TableLog, self).__init__(description=description)


class DictLog(BaseEntry):
    """Log a dict object to the report."""

    def __init__(self, dictionary, description=None):
        formatted_obj = fmt(dictionary)
        if len(formatted_obj) != 2 or formatted_obj[0] != 2:
            raise TypeError("Require a formatted object of mapping type")
        self.flattened_dict = flatten_formatted_object(formatted_obj)

        super(DictLog, self).__init__(description=description)


class FixLog(DictLog):
    """Log a fix message to the report."""

    def __init__(self, msg, description=None):
        if not msg or not isinstance(msg, dict):
            raise TypeError("Invalid format of fix message")

        super(FixLog, self).__init__(msg, description=description)


class Graph(BaseEntry):
    """Create a graph for the report."""

    def __init__(
        self,
        graph_type,
        graph_data,
        description=None,
        series_options=None,
        graph_options=None,
    ):
        """
        NOTE:
        When adding functionality to Graph, VALID_GRAPH_TYPES,
        VALID_CHART_TYPES, VALID_GRAPH_OPTIONS and
        VALID_SERIES_OPTIONS must be kept updated
        """
        self.VALID_GRAPH_TYPES = [
            "Line",
            "Scatter",
            "Bar",
            "Whisker",
            "Contour",
            "Hexbin",
        ]
        self.VALID_CHART_TYPES = ["Pie"]
        self.VALID_GRAPH_OPTIONS = ["xAxisTitle", "yAxisTitle", "legend"]
        self.VALID_SERIES_OPTIONS = ["colour"]

        self.graph_type = graph_type
        self.graph_data = graph_data

        if series_options is not None:
            self.assert_valid_series_options(series_options, graph_data)
        self.series_options = series_options

        if graph_options is not None:
            self.assert_valid_graph_options(graph_options)
        self.graph_options = graph_options

        self.type = "Graph"
        if graph_type in self.VALID_CHART_TYPES:
            self.discrete_chart = True
        elif graph_type in self.VALID_GRAPH_TYPES:
            self.discrete_chart = False
        else:
            raise ValueError(
                "Graph of type {!r} cannot " "be rendered".format(graph_type)
            )

        super(Graph, self).__init__(description=description)

    def assert_valid_graph_options(self, graph_options):
        for option in graph_options:
            if option not in self.VALID_GRAPH_OPTIONS:
                raise ValueError(
                    "Graph option {!r} " "is not valid".format(option)
                )

    def assert_valid_series_options(self, series_options, graph_data):
        for series_name in series_options:
            if series_name not in graph_data:
                raise ValueError(
                    "Series {!r} cannot be found in "
                    "graph data, cannot "
                    "apply series options".format(series_name)
                )
            for series_option in series_options[series_name]:
                if series_option not in self.VALID_SERIES_OPTIONS:
                    raise ValueError(
                        "Series Option: {!r} is not "
                        "valid (found in series "
                        "{!r})".format(series_option, series_name)
                    )


class Attachment(BaseEntry):
    """Entry representing a file attached to the report."""

    def __init__(self, filepath, description):
        self.source_path = filepath
        self.hash = path_utils.hash_file(filepath)
        self.orig_filename = os.path.basename(filepath)
        self.filesize = os.path.getsize(filepath)

        basename, ext = os.path.splitext(self.orig_filename)
        self.dst_path = "{basename}-{hash}-{filesize}{ext}".format(
            basename=basename, hash=self.hash, filesize=self.filesize, ext=ext
        )
        super(Attachment, self).__init__(description=description)


class MatPlot(Attachment):
    """Display a MatPlotLib graph in the report."""

    def __init__(
        self, pyplot, image_file_path, width=2, height=2, description=None
    ):
        self.width = float(width)
        self.height = float(height)
        dpi = 96
        pyplot.savefig(
            image_file_path, dpi=dpi, pad_inches=0, transparent=True
        )
        pyplot.close()
        super(MatPlot, self).__init__(
            filepath=image_file_path, description=description
        )


class CodeLog(BaseEntry):
    """Save source code to the report."""

    def __init__(self, code, language="python", description=None):
        if isinstance(code, basestring):
            self.code = code
        else:
            raise ValueError("Code must be a string")
        self.language = language
        super(CodeLog, self).__init__(description=description)


class Markdown(BaseEntry):
    """Save markdown to the report."""

    def __init__(self, message, description=None, escape=True):
        if isinstance(message, basestring):
            self.message = message
        else:
            raise ValueError("Message must be a string")
        self.escape = escape

        super(Markdown, self).__init__(description=description)
