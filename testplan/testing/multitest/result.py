"""
Defines the Result object and its sub-namepsaces.

The Result object is the interface used by testcases to make assertions and
log data. Entries contained in the result are copied into the Report object
after testcases have finished running.

"""
import inspect
import os
import platform
import re
import threading
from functools import wraps
from typing import Callable, Optional
import functools

from testplan import defaults
from testplan.common.utils.package import MOD_LOCK
from testplan.common.utils import comparison
from testplan.common.utils import strings
from testplan.defaults import STDOUT_STYLE
from testplan.common.report.base import SkipTestcaseException

from .entries import assertions, base
from .entries.schemas.base import registry as schema_registry
from .entries.stdout.base import registry as stdout_registry

IS_WIN = platform.system() == "Windows"


class ExceptionCapture:
    """
    Exception capture scope, will be used by exception related assertions.
    An instance of this class will be used as a context manager by
    exception related assertion methods.
    """

    def __init__(
        self,
        result,
        assertion_kls,
        exceptions,
        pattern=None,
        func=None,
        description=None,
        category=None,
    ):
        """
        :param result: Result object of the current testcase.
        :type result: ``testplan.testing.multitest.result.Result`` instance
        :param exceptions: List of expected exceptions.
        :type exceptions: ``list`` of exception classes.
        :param description: Description text for the exception capture context,
                            this will be the description for
                            the related assertion object.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        """

        self.result = result
        self.assertion_kls = assertion_kls
        self.exceptions = exceptions
        self.description = description
        self.pattern = pattern
        self.func = func
        self.category = category

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """
        Exiting the block and reporting what was thrown if anything.
        """
        exc_assertion = self.assertion_kls(
            raised_exception=exc_value,
            expected_exceptions=self.exceptions,
            pattern=self.pattern,
            func=self.func,
            category=self.category,
            description=self.description,
        )

        with MOD_LOCK:
            # TODO: see https://github.com/python/cpython/commit/85cf1d514b84dc9a4bcb40e20a12e1d82ff19f20
            caller_frame = inspect.stack()[1]

        exc_assertion.file_path = os.path.abspath(caller_frame[1])
        exc_assertion.line_no = caller_frame[2]

        # We cannot use `bind_entry` here as this block will
        # be run when an exception is raised
        # bind_entry replaced with assertion decorator
        stdout_registry.log_entry(
            entry=exc_assertion, stdout_style=self.result.stdout_style
        )
        self.result.entries.append(exc_assertion)
        return True


assertion_state = threading.local()


def report_target(func: Callable, ref_func: Callable = None) -> Callable:
    """
    Sets the decorated function's filepath and line-range in assertion state.
    If the target function is a parametrized function, should refer to its
    parametrized template to find information of the original function.

    :param func: The target function about which the information of
        source path and line range will be retrieved.
    :param ref_func: The parametrized template if `func` is a generated
        function, otherwise ``None``.
    """
    module = inspect.getmodule(ref_func or func)
    filepath = module.__file__ if module else None
    if filepath is None:
        try:
            filepath = inspect.getsourcefile(ref_func or func)
        except TypeError:
            pass

    try:
        lines, start = inspect.getsourcelines(ref_func or func)
        line_range = range(start, start + len(lines))
    except OSError:
        pass

    @wraps(func)
    def wrapper(*args, **kwargs):
        filepath_prev = getattr(assertion_state, "filepath", None)
        line_range_prev = getattr(assertion_state, "line_range", None)
        assertion_state.filepath = filepath
        assertion_state.line_range = line_range
        try:
            func(*args, **kwargs)
        finally:
            assertion_state.filepath = filepath_prev
            assertion_state.line_range = line_range_prev

    return wrapper


def assertion(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(result, *args, **kwargs):
        top_assertion = False
        if not getattr(assertion_state, "in_progress", False):
            assertion_state.in_progress = True
            top_assertion = True

        try:
            custom_style = kwargs.pop("custom_style", None)
            dryrun = kwargs.pop("dryrun", False)
            entry = func(result, *args, **kwargs)
            if top_assertion:
                with MOD_LOCK:
                    call_stack = inspect.stack()
                    try:
                        if getattr(assertion_state, "filepath", None) is None:
                            frame = call_stack[1]
                        else:
                            for frame in call_stack:
                                if (
                                    frame.filename == assertion_state.filepath
                                    and frame.lineno
                                    in assertion_state.line_range
                                ):
                                    break
                            else:
                                frame = call_stack[1]
                        entry.file_path = os.path.abspath(frame.filename)
                        entry.line_no = frame.lineno
                    finally:
                        # https://docs.python.org/3/library/inspect.html
                        del frame
                        del call_stack

                if custom_style is not None:
                    if not isinstance(custom_style, dict):
                        raise TypeError(
                            "Use `dict[str, str]` to specify custom CSS style"
                        )
                    entry.custom_style = custom_style

                assert isinstance(result, AssertionNamespace) or isinstance(
                    result, Result
                ), "Incorrect usage of assertion decorator"

                if isinstance(result, AssertionNamespace):
                    result = result.result

                if not dryrun:
                    result.entries.append(entry)

                stdout_registry.log_entry(
                    entry=entry, stdout_style=result.stdout_style
                )

                if not entry and not result.continue_on_failure:
                    raise AssertionError(entry)

            return entry
        finally:
            if top_assertion:
                assertion_state.in_progress = False

    return wrapper


class AssertionNamespace:
    """
    Base class for assertion namespaces.
    Users can inherit from this class to implement custom namespaces.
    """

    def __init__(self, result):
        self.result = result


class RegexNamespace(AssertionNamespace):
    """Contains logic for regular expression assertions."""

    @assertion
    def match(self, regexp, value, description=None, category=None, flags=0):
        """
        Checks if the given ``regexp`` matches the ``value``
        via ``re.match`` operation.

        .. code-block:: python

            result.regex.match(regexp='foo', value='foobar')

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be passed
                      to the ``re.match`` function.
        :type flags: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexMatch(
            regexp=regexp,
            string=value,
            flags=flags,
            description=description,
            category=category,
        )
        return entry

    @assertion
    def multiline_match(self, regexp, value, description=None, category=None):
        """
        Checks if the given ``regexp`` matches the ``value``
        via ``re.match`` operation, uses ``re.MULTILINE`` and ``re.DOTALL``
        flags implicitly.

        .. code-block:: python

            result.regex.multiline_match(
                regexp='first line.*second',
                value=os.linesep.join([
                    'first line',
                    'second line',
                    'third line'
                ]),
            )

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param description: text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status.
        :rtype: ``bool``
        """
        entry = assertions.RegexMatch(
            regexp=regexp,
            string=value,
            flags=re.MULTILINE | re.DOTALL,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def not_match(
        self, regexp, value, description=None, category=None, flags=0
    ):
        """
        Checks if the given ``regexp`` does not match the ``value``
        via ``re.match`` operation.

        .. code-block:: python

            result.regex.not_match('baz', 'foobar')

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be
                      passed to the ``re.match`` function.
        :type flags: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status.
        :rtype: ``bool``
        """
        entry = assertions.RegexMatchNotExists(
            regexp=regexp,
            string=value,
            flags=flags,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def multiline_not_match(
        self, regexp, value, description=None, category=None
    ):
        """
        Checks if the given ``regexp`` does not match the ``value``
        via ``re.match`` operation, uses ``re.MULTILINE`` and ``re.DOTALL``
        flags implicitly.

        .. code-block:: python

            result.regex.multiline_not_match(
                regexp='foobar',
                value=os.linesep.join([
                    'first line',
                    'second line',
                    'third line'
                ]),
            )

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexMatchNotExists(
            regexp=regexp,
            string=value,
            flags=re.MULTILINE | re.DOTALL,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def search(self, regexp, value, description=None, category=None, flags=0):
        """
        Checks if the given ``regexp`` exists in the ``value``
        via ``re.search`` operation.

        .. code-block:: python

            result.regex.search('bar', 'foobarbaz')

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be passed
                      to the ``re.search`` function.
        :type flags: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexSearch(
            regexp=regexp,
            string=value,
            flags=flags,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def search_empty(
        self, regexp, value, description=None, category=None, flags=0
    ):
        """
        Checks if the given ``regexp`` does not exist in the ``value``
        via ``re.search`` operation.

        .. code-block:: python

            result.regex.search_empty('aaa', 'foobarbaz')

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be passed
                      to the ``re.search`` function.
        :type flags: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexSearchNotExists(
            regexp=regexp,
            string=value,
            flags=flags,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def findall(
        self,
        regexp,
        value,
        description=None,
        category=None,
        flags=0,
        condition=None,
    ):
        """
        Checks if there are one or more matches of the ``regexp`` exist in
        the ``value`` via ``re.finditer``.
        Can apply further assertions via ``condition`` func.

        .. code-block:: python

            result.regex.findall(
                regexp='foo',
                value='foo foo foo bar bar foo bar',
                condition=lambda num_matches: 2 < num_matches < 5,
            )

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be passed
                      to the ``re.finditer`` function.
        :type flags: ``int``
        :param condition: A callable that accepts a single argument,
                          which is the number of matches (int).
        :type condition: ``callable``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexFindIter(
            regexp=regexp,
            string=value,
            description=description,
            flags=flags,
            condition=condition,
            category=category,
        )

        return entry

    @assertion
    def matchline(
        self, regexp, value, description=None, category=None, flags=0
    ):
        r"""
        Checks if the given ``regexp`` returns a match
        (``re.match``) for any of the lines in the ``value``.

        .. code-block:: python

            result.regex.matchline(
                regexp=re.compile(r'\w+ line$'),
                value=os.linesep.join([
                    'first line',
                    'second aaa',
                    'third line'
                ]),
            )

        :param regexp: String pattern or compiled regexp object.
        :type regexp: ``str`` or compiled regex
        :param value: String to match against.
        :type value: ``str``
        :param flags: Regex flags that will be passed
                      to the ``re.match`` function.
        :type flags: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.RegexMatchLine(
            regexp=regexp,
            string=value,
            description=description,
            flags=flags,
            category=category,
        )

        return entry


class TableNamespace(AssertionNamespace):
    """Contains logic for regular expression assertions."""

    @assertion
    def column_contain(
        self,
        table,
        values,
        column,
        description=None,
        category=None,
        limit=None,
        report_fails_only=False,
    ):
        """
        Checks if all of the values of a table's
        column contain values from a given list.

        .. code-block:: python

            result.table.column_contain(
                table=[
                    ['symbol', 'amount'],
                    ['AAPL', 12],
                    ['GOOG', 21],
                    ['FB', 32],
                    ['AMZN', 5],
                    ['MSFT', 42]
                ],
                values=['AAPL', 'AMZN'],
                column='symbol',
            )

        :param table: Tabular data
        :type table: ``list`` of ``list`` or ``list`` of ``dict``.
        :param values: Values that will be checked against each cell.
        :type values: ``iterable`` of ``object``
        :param column: Column name to check.
        :type column: ``str``
        :param limit: Maximum number of rows to process,
                      can be used for limiting output.
        :type limit: ``int``
        :param report_fails_only: Filtering option, output will contain failures
                                  only if this argument is True.
        :type report_fails_only: ``bool``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.ColumnContain(
            table=table,
            values=values,
            column=column,
            limit=limit,
            report_fails_only=report_fails_only,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def match(
        self,
        actual,
        expected,
        description=None,
        category=None,
        include_columns=None,
        exclude_columns=None,
        report_all=True,
        fail_limit=0,
    ):
        r"""
        Compares two tables, uses equality for each table cell for plain
        values and supports regex / custom comparators as well.

        If the columns of the two tables are not the same,
        either ``include_columns`` or ``exclude_columns`` arguments
        must be used to have column uniformity.

        .. code-block:: python

            result.table.match(
                actual=[
                    ['name', 'age'],
                    ['Bob', 32],
                    ['Susan', 24],
                ],
                expected=[
                    ['name', 'age'],
                    ['Bob', 33],
                    ['David', 24],
                ]
            )

            result.table.match(
                actual=[
                    ['name', 'age'],
                    ['Bob', 32],
                    ['Susan', 24],
                ],
                expected=[
                    ['name', 'age'],
                    [re.compile(r'^B\w+'), 33],
                    ['David', lambda age: 20 < age < 50],
                ]
            )

        :param actual: Tabular data
        :type actual: ``list`` of ``list`` or ``list`` of ``dict``.
        :param expected: Tabular data, which can contain custom comparators.
        :type expected: ``list`` of ``list`` or ``list`` of ``dict``.
        :param include_columns: List of columns to include
                                in the comparison. Cannot be used
                                with ``exclude_columns``.
        :type include_columns: ``list`` of ``str``
        :param exclude_columns: List of columns to exclude
                                from the comparison. Cannot be used
                                with ``include_columns``.
        :type exclude_columns: ``list`` of ``str``
        :param report_all: Boolean flag for configuring output.
                           If True then all columns of the original
                           table will be displayed.
        :type report_all: ``bool``
        :param fail_limit: Max number of failures before aborting
                           the comparison run. Useful for large
                           tables, when we want to stop after we have N rows
                           that fail the comparison.
        :type fail_limit: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.TableMatch(
            table=actual,
            expected_table=expected,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            report_all=report_all,
            fail_limit=fail_limit,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def diff(
        self,
        actual,
        expected,
        description=None,
        category=None,
        include_columns=None,
        exclude_columns=None,
        report_all=True,
        fail_limit=0,
    ):
        r"""
        Find differences of two tables, uses equality for each table cell
        for plain values and supports regex / custom comparators as well.
        The result will contain only failing comparisons.

        If the columns of the two tables are not the same,
        either ``include_columns`` or ``exclude_columns`` arguments
        must be used to have column uniformity.

        .. code-block:: python

            result.table.diff(
                actual=[
                    ['name', 'age'],
                    ['Bob', 32],
                    ['Susan', 24],
                ],
                expected=[
                    ['name', 'age'],
                    ['Bob', 33],
                    ['David', 24],
                ]
            )

            result.table.diff(
                actual=[
                    ['name', 'age'],
                    ['Bob', 32],
                    ['Susan', 24],
                ],
                expected=[
                    ['name', 'age'],
                    [re.compile(r'^B\w+'), 33],
                    ['David', lambda age: 20 < age < 50],
                ]
            )

        :param actual: Tabular data
        :type actual: ``list`` of ``list`` or ``list`` of ``dict``.
        :param expected: Tabular data, which can contain custom comparators.
        :type expected: ``list`` of ``list`` or ``list`` of ``dict``.
        :param include_columns: List of columns to include
                                in the comparison. Cannot be used
                                with ``exclude_columns``.
        :type include_columns: ``list`` of ``str``
        :param exclude_columns: List of columns to exclude
                                from the comparison. Cannot be used
                                with ``include_columns``.
        :type exclude_columns: ``list`` of ``str``
        :param report_all: Boolean flag for configuring output.
                           If True then all columns of the original
                           table will be displayed.
        :type report_all: ``bool``
        :param fail_limit: Max number of failures before aborting
                           the comparison run. Useful for large
                           tables, when we want to stop after we have N rows
                           that fail the comparison.
        :type fail_limit: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.TableDiff(
            table=actual,
            expected_table=expected,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            report_all=report_all,
            fail_limit=fail_limit,
            report_fail_only=True,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def log(self, table, display_index=False, description=None):
        """
        Logs a table to the report.

        .. code-block:: python

            result.table.log(
                table=[
                    ['name', 'age', 'gender'],
                    ['Bob', 32, 'M'],
                    ['Susan', 24, 'F'],
                ]
            )

        :param table: Tabular data.
        :type table: ``list`` of ``list`` or ``list`` of ``dict``
        :param display_index: Flag whether to display row indices.
        :type display_index: ``bool``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: Always returns True, this is not an assertion so it cannot
            fail.
        :rtype: ``bool``
        """
        entry = base.TableLog(
            table=table, display_index=display_index, description=description
        )
        return entry


class XMLNamespace(AssertionNamespace):
    """Contains logic for XML related assertions."""

    @assertion
    def check(
        self,
        element,
        xpath,
        description=None,
        category=None,
        tags=None,
        namespaces=None,
    ):
        """
        Checks if given xpath and tags exist in the XML body.
        Supports namespace based matching as well.

        .. code-block:: python

            result.xml.check(
                element='''
                <Root>
                    <Test>Value1</Test>
                    <Test>Value2</Test>
                </Root>
                ''',
                xpath='/Root/Test',
                tags=['Value1', 'Value2'],
            )

            result.xml.check(
                element='''
                <SOAP-ENV:Envelope
                    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                    <SOAP-ENV:Header/>
                    <SOAP-ENV:Body>
                        <ns0:message
                        xmlns:ns0="http://testplan">Hello world!</ns0:message>
                    </SOAP-ENV:Body>
                </SOAP-ENV:Envelope>
                ''',
                xpath='//*/a:message',
                tags=[re.compile(r'Hello*')],
                namespaces={"a": "http://testplan"},
            )

        :param element: XML element
        :type element: ``str`` or ``lxml.etree.Element``
        :param xpath: XPath expression to be used for navigation & check.
        :type xpath: ``str``
        :param tags: Tag values to match against in the given xpath.
        :type tags: ``list`` of ``str`` or compiled regex patterns
        :param namespaces: Prefix mapping for xpath expressions.
                           (namespace prefixes as keys and URIs for values.)
        :type namespaces: ``dict``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.XMLCheck(
            element=element,
            xpath=xpath,
            tags=tags,
            namespaces=namespaces,
            description=description,
            category=category,
        )

        return entry


class DictNamespace(AssertionNamespace):
    """Contains logic for Dictionary related assertions."""

    @assertion
    def check(
        self,
        dictionary,
        description=None,
        category=None,
        has_keys=None,
        absent_keys=None,
    ):
        """
        Checks for existence / absence of dictionary keys, uses top
        level keys in case of nested dictionaries.

        .. code-block:: python

            result.dict.check(
                dictionary={
                    'foo': 1, 'bar': 2, 'baz': 3,
                },
                has_keys=['foo', 'alpha'],
                absent_keys=['bar', 'beta']
            )

        :param dictionary: Dict object to check.
        :type dictionary: ``dict``
        :param has_keys: List of keys to check for existence.
        :type has_keys: ``list`` or ``object`` (items must be hashable)
        :param absent_keys: List of keys to check for absence.
        :type absent_keys: ``list`` or ``object`` (items must be hashable)
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.DictCheck(
            dictionary=dictionary,
            has_keys=has_keys,
            absent_keys=absent_keys,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def match(
        self,
        actual,
        expected,
        description=None,
        category=None,
        include_keys=None,
        exclude_keys=None,
        report_mode=comparison.ReportOptions.ALL,
        actual_description=None,
        expected_description=None,
        value_cmp_func=comparison.COMPARE_FUNCTIONS["native_equality"],
    ):
        r"""
        Matches two dictionaries, supports nested data. Custom
        comparators can be used as values on the ``expected`` dict.

        .. code-block:: python

            from testplan.common.utils import comparison

            result.dict.match(
                actual={
                    'foo': 1,
                    'bar': 2,
                },
                expected={
                    'foo': 1,
                    'bar': 5,
                    'extra-key': 10,
                },
            )

            result.dict.match(
                actual={
                    'foo': [1, 2, 3],
                    'bar': {'color': 'blue'},
                    'baz': 'hello world',
                },
                expected={
                    'foo': [1, 2, lambda v: isinstance(v, int)],
                    'bar': {
                        'color': comparison.In(['blue', 'red', 'yellow'])
                    },
                    'baz': re.compile(r'\w+ world'),
                }
            )

        :param actual: Original dictionary.
        :type actual: ``dict``.
        :param expected: Comparison dictionary, can contain custom comparators
                         (e.g. regex, lambda functions)
        :type expected: ``dict``
        :param include_keys: Keys to exclusively consider in the comparison.
        :type include_keys: ``list`` of ``object`` (items must be hashable)
        :param exclude_keys: Keys to ignore in the comparison.
        :type exclude_keys: ``list`` of ``object`` (items must be hashable)
        :param report_mode: Specify which comparisons should be kept and
                            reported. Default option is to report all
                            comparisons but this can be restricted if desired.
                            See ReportOptions enum for more detail.
        :type report_mode: ``testplan.common.utils.comparison.ReportOptions``
        :param actual_description: Column header description for original dict.
        :type actual_description: ``str``
        :param expected_description: Column header
                                    description for expected dict.
        :type expected_description: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :param value_cmp_func: Function to use to compare values in expected
                               and actual dicts. Defaults to using
                               `operator.eq()`.
        :type value_cmp_func: ``Callable[[Any, Any], bool]``

        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.DictMatch(
            value=actual,
            expected=expected,
            description=description,
            include_keys=include_keys,
            exclude_keys=exclude_keys,
            report_mode=report_mode,
            expected_description=expected_description,
            actual_description=actual_description,
            category=category,
            value_cmp_func=value_cmp_func,
        )

        return entry

    @assertion
    def match_all(
        self,
        values,
        comparisons,
        description=None,
        category=None,
        key_weightings=None,
    ):
        """
        Match multiple unordered dictionaries.

        Initially all value/expected comparison combinations are
        evaluated and converted to an error weight.

        If certain keys are more important than others, it is possible
        to give them additional weighting during the comparison,
        by specifying a "key_weightings" dict. The default weight of
        a mismatch is 100.

        The values/comparisons permutation that results in
        the least error appended to the report.

        .. code-block:: python

            result.dict.match_all(
                values=[
                    {'foo': 12, ...},
                    {'foo': 13, ...},
                    ...
                ],
                comparisons=[
                    Expected({'foo': 12, ...}),
                    Expected({'foo': 15, ...})
                    ...
                ],
                # twice the default weight of 100
                key_weightings={'foo': 200})

        :param values: Original values.
        :type values: ``list`` of ``dict``
        :param comparisons: Comparison objects.
        :type comparisons: ``list`` of
                           ``testplan.common.utils.comparison.Expected``
        :param key_weightings: Per-key overrides that specify a different
                               weight for different keys.
        :type key_weightings: ``dict``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.DictMatchAll(
            values=values,
            comparisons=comparisons,
            key_weightings=key_weightings,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def log(self, dictionary, description=None):
        """
        Logs a dictionary to the report.

        .. code-block:: python

            result.dict.log(
                dictionary={
                    'foo': [1, 2, 3],
                    'bar': {'color': 'blue'},
                    'baz': 'hello world',
                }
            )

        :param dictionary: Dict object to log.
        :type dictionary: ``dict``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: Always returns True, this is not an assertion so it cannot
            fail.
        :rtype: ``bool``
        """
        entry = base.DictLog(dictionary=dictionary, description=description)

        return entry


class FixNamespace(AssertionNamespace):
    """Contains assertion logic that operates on fix messages."""

    @assertion
    def check(
        self,
        msg,
        description=None,
        category=None,
        has_tags=None,
        absent_tags=None,
    ):
        """
        Checks existence / absence of tags in a Fix message.
        Checks top level tags only.

        .. code-block:: python

            result.fix.check(
                msg={
                    36: 6,
                    22: 5,
                    55: 2,
                    38: 5,
                    555: [ .. more nested data here ... ]
                },
                has_tags=[26, 22, 11],
                absent_tags=[444, 555],
            )

        :param msg: Fix message.
        :type msg: ``dict``
        :param has_tags: List of tags to check for existence.
        :type has_tags: ``list`` of ``object`` (items must be hashable)
        :param absent_tags: List of tags to check for absence.
        :type absent_tags: ``list`` of ``object`` (items must be hashable)
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.FixCheck(
            msg=msg,
            has_tags=has_tags,
            absent_tags=absent_tags,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def match(
        self,
        actual,
        expected,
        description=None,
        category=None,
        include_tags=None,
        exclude_tags=None,
        report_mode=comparison.ReportOptions.ALL,
        actual_description=None,
        expected_description=None,
    ):
        """
        Matches two FIX messages, supports repeating groups (nested data).
        Custom comparators can be used as values on the ``expected`` msg.

        .. code-block:: python

            result.fix.match(
                actual={
                    36: 6,
                    22: 5,
                    55: 2,
                    38: 5,
                    555: [ .. more nested data here ... ]
                },
                expected={
                    36: 6,
                    22: 5,
                    55: lambda val: val in [2, 3, 4],
                    38: 5,
                    555: [ .. more nested data here ... ]
                }
            )

        :param actual: Original FIX message.
        :type actual: ``dict``
        :param expected: Expected FIX message, can include compiled
                         regex patterns or callables for
                         advanced comparison.
        :type expected: ``dict``
        :param include_tags: Tags to exclusively consider in the comparison.
        :type include_tags: ``list`` of ``object`` (items must be hashable)
        :param exclude_tags: Keys to ignore in the comparison.
        :type exclude_tags: ``list`` of ``object`` (items must be hashable)
        :param report_mode: Specify which comparisons should be kept and
                            reported. Default option is to report all
                            comparisons but this can be restricted if desired.
                            See ReportOptions enum for more detail.
        :type report_mode: ``testplan.common.utils.comparison.ReportOptions``
        :param actual_description: Column header description for original msg.
        :type actual_description: ``str``
        :param expected_description: Column header
                                     description for expected msg.
        :type expected_description: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``

        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.FixMatch(
            value=actual,
            expected=expected,
            description=description,
            category=category,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
            report_mode=report_mode,
            expected_description=expected_description,
            actual_description=actual_description,
        )

        return entry

    @assertion
    def match_all(
        self,
        values,
        comparisons,
        description=None,
        category=None,
        tag_weightings=None,
    ):
        """
        Match multiple unordered FIX messages.

        Initially all value/expected comparison combinations are
        evaluated and converted to an error weight.

        If certain fix tags are more important than others (e.g. ID FIX tags),
        it is possible to give them additional weighting during the comparison,
        by specifying a "tag_weightings" dict.

        The default weight of a mismatch is 100.

        The values/comparisons permutation that results in
        the least error appended to the report.


        .. code-block:: python

            result.dict.match_all(
                values=[
                    { 36: 6, 22: 5, 55: 2, ...},
                    { 36: 7, ...},
                    ...
                ],
                comparisons=[
                    Expected({ 36: 6, 22: 5, 55: 2, ...},),
                    Expected({ 36: 7, ...})
                    ...
                ],
                # twice the default weight of 100
                key_weightings={36: 200})


        :param values: Original values.
        :type values: ``list`` of ``dict``
        :param comparisons: Comparison objects.
        :type comparisons: ``list`` of
                           ``testplan.common.utils.comparison.Expected``
        :param tag_weightings: Per-tag overrides that specify a different
                               weight for different tags.
        :type tag_weightings: ``dict``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.FixMatchAll(
            values=values,
            comparisons=comparisons,
            tag_weightings=tag_weightings,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def log(self, msg, description=None):
        """
        Logs a fix message to the report.

        .. code-block:: python

            result.fix.log(
                msg={
                    36: 6,
                    22: 5,
                    55: 2,
                    38: 5,
                    555: [ .. more nested data here ... ]
                }
            )

        :param msg: Fix message.
        :type msg: ``dict`` or ``pyfixmsg.fixmessage.FixMessage``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: Always returns True, this is not an assertion so it cannot
            fail.
        :rtype: ``bool``
        """
        entry = base.FixLog(msg=msg, description=description)

        return entry


class Result:
    """
    Contains assertion methods and namespaces for generating test data.
    A new instance of ``Result`` object is passed to each testcase when a
    suite is run.
    """

    namespaces = {
        "regex": RegexNamespace,
        "table": TableNamespace,
        "xml": XMLNamespace,
        "dict": DictNamespace,
        "fix": FixNamespace,
    }

    def __init__(
        self,
        stdout_style=None,
        continue_on_failure=True,
        _group_description=None,
        _parent=None,
        _summarize=False,
        _num_passing=defaults.SUMMARY_NUM_PASSING,
        _num_failing=defaults.SUMMARY_NUM_FAILING,
        _scratch=None,
    ):

        self.entries = []
        self.attachments = []

        self.stdout_style = stdout_style or STDOUT_STYLE
        self.continue_on_failure = continue_on_failure

        for key, value in self.get_namespaces().items():
            if hasattr(self, key):
                raise AttributeError(
                    "Name clash, cannot assign namespace: {}".format(key)
                )
            setattr(self, key, value(result=self))

        self._parent = _parent
        self._group_description = _group_description
        self._summarize = _summarize
        self._num_passing = _num_passing
        self._num_failing = _num_failing
        self._scratch = _scratch

    def subresult(self):
        """Subresult object to append/prepend assertions on another."""
        return self.__class__(
            stdout_style=self.stdout_style,
            continue_on_failure=self.continue_on_failure,
            _group_description=self._group_description,
            _parent=self._parent,
            _summarize=self._summarize,
            _num_passing=self._num_passing,
            _num_failing=self._num_failing,
            _scratch=self._scratch,
        )

    def append(self, result):
        """Append entries from another result."""
        self.entries += result.entries

    def prepend(self, result):
        """Prepend entries from another result."""
        self.entries = result.entries + self.entries

    def __enter__(self):
        if self._parent is None:
            raise RuntimeError(
                "Cannot use root level result objects as context managers."
                " Use `with result.group(...)` instead."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._summarize:
            entry_group = base.Summary(
                entries=self.entries,
                description=self._group_description,
                num_passing=self._num_passing,
                num_failing=self._num_failing,
            )
        else:
            entry_group = base.Group(
                entries=self.entries, description=self._group_description
            )
        self._parent.entries.append(entry_group)
        self._parent.attachments.extend(self.attachments)
        return exc_type is None  # re-raise errors if there is any

    def get_namespaces(self):
        """
        This method can be overridden for enabling
        custom assertion namespaces for child classes.
        """
        return self.namespaces or {}

    def group(
        self,
        description=None,
        summarize=False,
        num_passing=defaults.SUMMARY_NUM_PASSING,
        num_failing=defaults.SUMMARY_NUM_FAILING,
    ):
        """
        Creates an assertion group or summary, which is helpful
        for formatting assertion data on certain output
        targets (e.g. PDF, JSON) and reducing the amount of
        content that gets displayed.

        Should be used as a context manager.

        .. code-block:: python

            # Group and sub groups
            with result.group(description='Custom group description') as group:
                group.not_equal(2, 3, description='Assertion within a group')
                group.greater(5, 3)
                with group.group() as sub_group:
                    sub_group.less(6, 3, description='Assertion in sub group')


            # Summary example
            with result.group(
                summarize=True,
                num_passing=4,
                num_failing=10,
            ) as group:
                for i in range(500):
                    # First 4 passing assertions will be displayed
                    group.equal(i, i)
                    # First 10 failing assertions will be displayed
                    group.equal(i, i + 1)


        :param description: Text description for the assertion group.
        :type description: ``str``
        :param summarize: Flag for enabling summarization.
        :type summarize: ``bool``
        :param num_passing: Max limit for number of passing
                            assertions per category & assertion type.
        :type num_passing: ``int``
        :param num_failing: Max limit for number of failing
                            assertions per category & assertion type.
        :type num_failing: ``int``
        :return: A new result object that refers the current result as a parent.
        :rtype: Result object
        """
        return Result(
            stdout_style=self.stdout_style,
            continue_on_failure=self.continue_on_failure,
            _group_description=description,
            _parent=self,
            _summarize=summarize,
            _num_passing=num_passing,
            _num_failing=num_failing,
            _scratch=self._scratch,
        )

    @property
    def passed(self):
        """Entries stored passed status."""
        return all(getattr(entry, "passed", True) for entry in self.entries)

    @assertion
    def log(self, message, description=None, flag=None):
        """
        Create a string message entry, can be used for providing additional
        context related to test steps.

        .. code-block:: python

            result.log('Custom log message ...')

        :param message: Log message
        :type message: ``str`` or instance
        :param description: Text description for the assertion.
        :type description: ``str``
        :param flag: Custom flag of the assertion which is reserved and can
            be used for some special purpose.
        :param flag: ``str`` or ``NoneType``
        :return: Always returns True, this is not an assertion so it cannot
            fail.
        :rtype: ``bool``
        """
        entry = base.Log(message=message, description=description, flag=flag)

        return entry

    @assertion
    def markdown(self, message, description=None, escape=True):
        """
        Create a markdown message entry, can be used for providing additional
        context related to test steps.

        .. code-block:: python

            result.markdown(
                'Markdown string ....',
                description='Test',
                escape=False
            )

        :param message: Markdown string
        :type message: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param escape: Escape html.
        :param escape: ``bool``
        :return: ``True``
        :rtype: ``bool``
        """
        entry = base.Markdown(
            message=message, description=description, escape=escape
        )

        return entry

    @assertion
    def log_html(self, code, description="Embedded HTML"):
        """
        Create a markdown message entry without escape, can be used for
        providing additional context related to test steps.

        :param code: HTML code string. Tag <script> will not be executed.
        :type code: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: ``True``
        :rtype: ``bool``
        """
        return self.markdown(code, description=description, escape=False)

    @assertion
    def log_code(self, code, language="python", description=None):
        """
        Create a codelog message entry which contains code snippet, can
        be used for providing additional context related to test steps.

        :param code: The source code string.
        :type code: ``str``
        :param language: The language of source code. e.g. js, xml, python,
            java, c, cpp, bash. Defaults to python.
        :type language: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: ``True``
        :rtype: ``bool``
        """
        entry = base.CodeLog(
            code=code, language=language, description=description
        )

        return entry

    @assertion
    def fail(
        self,
        message: str,
        description: Optional[str] = None,
        flag: Optional[str] = None,
        category: Optional[str] = None,
    ) -> assertions.Fail:
        """
        Failure assertion, can be used for explicitly failing a testcase.
        The message will be included by email exporter. Most common usage is
        within a conditional block.

        .. code-block:: python

            if some_condition:
                result.fail('Unexpected failure: {}'.format(...))

        :param description: Text description of the failure.
        :param category: Custom category that will be used for summarization.
        :param flag: custom flag - reserved parameter
        :return: ``False``
        """
        entry = assertions.Fail(
            description=description,
            message=message,
            category=category,
            flag=flag,
        )

        return entry

    def conditional_log(
        self,
        condition,
        log_message,
        log_description,
        fail_description,
        flag=None,
    ):
        """
        A compound assertion that does result.log() or result.fail()
        depending on the truthiness of condition.

        .. code-block:: python

            result.conditional_log(
                some_condition,
                log_message,
                log_description,
                fail_description,
            )

        is a shortcut for writing:

        .. code-block:: python

            if some_condition:
                result.log(log_message, description=log_description)
            else:
                result.fail(fail_description)

        :param condition: Value to be evaluated for truthiness
        :param condition: ``object``
        :param log_message: Message to pass to result.log if condition
            evaluates to True.
        :type log_message: ``str``
        :param log_description: Description to pass to result.log if
            condition evaluates to True.
        :type log_description: ``str``
        :param fail_description: Description to pass to result.fail if
            condition evaluates to False.
        :type fail_description: ``str``
        :param flag: Custom flag of the assertion which is reserved and can
            be used for some special purpose.
        :return: ``True``
        :rtype: ``bool``
        """
        if condition:
            if log_description:
                return self.log(
                    log_message, description=log_description, flag=flag
                )
        else:
            return self.fail(fail_description, flag=flag)

    @assertion
    def true(self, value, description=None, category=None):
        """
        Boolean assertion, checks if ``value`` is truthy.

        .. code-block:: python

            result.true(some_obj, 'Custom description')

        :param value: Value to be evaluated for truthiness.
        :type value: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.IsTrue(
            value, description=description, category=category
        )

        return entry

    @assertion
    def false(self, value, description=None, category=None):
        """
        Boolean assertion, checks if ``value`` is falsy.

        .. code-block:: python

            result.false(some_obj, 'Custom description')

        :param value: Value to be evaluated for falsiness.
        :type value: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.IsFalse(
            value, description=description, category=category
        )

        return entry

    @assertion
    def equal(self, actual, expected, description=None, category=None):
        """
        Equality assertion, checks if ``actual == expected``.
        Can be used via shortcut: ``result.eq``.

        .. code-block:: python

            result.equal('foo', 'foo', 'Custom description')

        :param actual: First (actual) value of the comparison.
        :type actual: ``object``
        :param expected: Second (expected) value of the comparison.
        :type expected: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.Equal(
            actual, expected, description=description, category=category
        )

        return entry

    @assertion
    def not_equal(self, actual, expected, description=None, category=None):
        """
        Inequality assertion, checks if ``actual != expected``.
        Can be used via shortcut: ``result.ne``.

        .. code-block:: python

            result.not_equal('foo', 'bar', 'Custom description')

        :param actual: First (actual) value of the comparison.
        :type actual: ``object``
        :param expected: Second (expected) value of the comparison.
        :type expected: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.NotEqual(
            actual, expected, description=description, category=category
        )

        return entry

    @assertion
    def less(self, first, second, description=None, category=None):
        """
        Checks if ``first < second``.
        Can be used via shortcut: ``result.lt``

        .. code-block:: python

            result.less(3, 5, 'Custom description')

        :param first: Left side of the comparison.
        :type first: ``object``
        :param second: Right side of the comparison.
        :type second: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.Less(
            first, second, description=description, category=category
        )

        return entry

    @assertion
    def greater(self, first, second, description=None, category=None):
        """
        Checks if ``first > second``.
        Can be used via shortcut: ``result.gt``

        .. code-block:: python

            result.greater(5, 3, 'Custom description')

        :param first: Left side of the comparison.
        :type first: ``object``
        :param second: Right side of the comparison.
        :type second: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.Greater(
            first, second, description=description, category=category
        )

        return entry

    @assertion
    def less_equal(self, first, second, description=None, category=None):
        """
        Checks if ``first <= second``.
        Can be used via shortcut: ``result.le``

        .. code-block:: python

            result.less_equal(5, 3, 'Custom description')

        :param first: Left side of the comparison.
        :type first: ``object``
        :param second: Right side of the comparison.
        :type second: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.LessEqual(
            first, second, description=description, category=category
        )

        return entry

    @assertion
    def greater_equal(self, first, second, description=None, category=None):
        """
        Checks if ``first >= second``.
        Can be used via shortcut: ``result.ge``

        .. code-block:: python

            result.greater_equal(5, 3, 'Custom description')

        :param first: Left side of the comparison.
        :type first: ``object``
        :param second: Right side of the comparison.
        :type second: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.GreaterEqual(
            first, second, description=description, category=category
        )

        return entry

    # Shortcut aliases for basic comparators
    eq = equal
    ne = not_equal
    lt = less
    gt = greater
    le = less_equal
    ge = greater_equal

    @assertion
    def isclose(
        self,
        first,
        second,
        rel_tol=1e-09,
        abs_tol=0.0,
        description=None,
        category=None,
    ):
        """
        Checks if ``first`` and ``second`` are approximately equal.

        .. code-block:: python

            result.isclose(99.99, 100, 0.001, 0.0, 'Custom description')

        :param first: The first item to be compared for approximate equality.
        :type first: ``numbers.Number``
        :param second: The second item to be compared for approximate equality.
        :type second: ``numbers.Number``
        :param rel_tol: The relative tolerance.
        :type rel_tol: ``numbers.Real``
        :param abs_tol: The minimum absolute tolerance level.
        :type abs_tol: ``numbers.Real``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.IsClose(
            first,
            second,
            rel_tol,
            abs_tol,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def contain(self, member, container, description=None, category=None):
        """
        Checks if ``member in container``.

        .. code-block:: python

            result.contain(1, [1, 2, 3, 4], 'Custom description')

        :param member: Item to be checked for existence in the container.
        :type member: ``object``
        :param container: Container object, should support
                          item lookup operations.
        :type container: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.Contain(
            member, container, description=description, category=category
        )

        return entry

    @assertion
    def not_contain(self, member, container, description=None, category=None):
        """
        Checks if ``member not in container``.

        .. code-block:: python

            result.not_contain(5, [1, 2, 3, 4], 'Custom description')

        :param member: Item to be checked for absence from the container.
        :type member: ``object``
        :param container: Container object, should support
                          item lookup operations.
        :type container: ``object``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.NotContain(
            member, container, description=description, category=category
        )

        return entry

    @assertion
    def equal_slices(
        self, actual, expected, slices, description=None, category=None
    ):
        """
        Checks if given slices of ``actual`` and ``expected`` are equal.

        .. code-block:: python

            result.equal_slices(
                [1, 2, 3, 4, 5, 6, 7, 8],
                ['a', 'b', 3, 4, 'c', 'd', 7, 8],
                slices=[slice(2, 4), slice(6, 8)],
                description='Comparison of slices'
            )

        :param actual: First (actual) value of the comparison.
        :type actual: ``object`` that supports slice operations.
        :param expected: Second (expected) value of the comparison.
        :type expected: ``object`` that supports slice operations.
        :param slices: Slices that will be applied
                       to ``actual`` and ``expected``.
        :type slices: ``list`` of ``slice``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.EqualSlices(
            expected=expected,
            actual=actual,
            slices=slices,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def equal_exclude_slices(
        self, actual, expected, slices, description=None, category=None
    ):
        """
        Checks if items that exist outside the given slices of
        ``actual`` and ``expected`` are equal.

        .. code-block:: python

            result.equal_exclude_slices(
                [1, 2, 3, 4, 5, 6, 7, 8],
                ['a', 'b', 3, 4, 'c', 'd', 'e', 'f'],
                slices=[slice(0, 2), slice(4, 8)],
                description='Comparison of slices (exclusion)'
            )

        :param actual: First (actual) value of the comparison.
        :type actual: ``object`` that supports slice operations.
        :param expected: Second (expected) value of the comparison.
        :type expected: ``object`` that supports slice operations.
        :param slices: Slices that will be used for exclusion of items
                       from ``actual`` and ``expected``.
        :type slices: ``list`` of ``slice``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.EqualExcludeSlices(
            expected=expected,
            actual=actual,
            slices=slices,
            description=description,
            category=category,
        )

        return entry

    def raises(
        self,
        exceptions,
        description=None,
        category=None,
        pattern=None,
        func=None,
    ):
        """
        Checks if given code block raises certain type(s) of exception(s).
        Supports further checks via ``pattern`` and ``func`` arguments.

        .. code-block:: python

            with result.raises(KeyError):
                {'foo': 3}['bar']


            with result.raises(ValueError, pattern='foo')
                raise ValueError('abc foobar xyz')


            def check_exception(exc):
                ...

            with result.raises(TypeError, func=check_exception):
                raise TypeError(...)

        :param exceptions: Exception types to check.
        :type exceptions: ``list`` of ``Exception`` classes
                          or a single ``Exception`` class
        :param pattern: String pattern that will be
                        searched (``re.searched``) within exception message.
        :type pattern: ``str`` or compiled regex object
        :param func: Callable that accepts a single argument
                                (the exception object)
        :type func: ``callable``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        return ExceptionCapture(
            result=self,
            assertion_kls=assertions.ExceptionRaised,
            exceptions=exceptions,
            description=description,
            category=category,
            func=func,
            pattern=pattern,
        )

    def not_raises(
        self,
        exceptions,
        description=None,
        category=None,
        pattern=None,
        func=None,
    ):
        """
        Checks if given code block does not raise
        certain type(s) of exception(s).

        Supports further checks via ``pattern`` and ``func`` arguments.

        .. code-block:: python

            with result.not_raises(AttributeError):
                {'foo': 3}['bar']


            with result.raises(ValueError, pattern='foo')
                raise ValueError('abc xyz')


            def check_exception(exc):
                ...

            with result.raises(TypeError, func=check_exception):
                raise TypeError(...)

        :param exceptions: Exception types to check.
        :type exceptions: ``list`` of ``Exception`` classes
                          or a single ``Exception`` class
        :param pattern: String pattern that will be
                        searched (``re.searched``) within exception message.
        :type pattern: ``str`` or compiled regex object
        :param func: Callable that accepts a single argument
                                (the exception object)
        :type func: ``callable``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param category: Custom category that will be used for summarization.
        :type category: ``str``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        return ExceptionCapture(
            result=self,
            assertion_kls=assertions.ExceptionNotRaised,
            exceptions=exceptions,
            description=description,
            category=category,
            func=func,
            pattern=pattern,
        )

    @assertion
    def diff(
        self,
        first,
        second,
        ignore_space_change=False,
        ignore_whitespaces=False,
        ignore_blank_lines=False,
        unified=False,
        context=False,
        description=None,
        category=None,
    ):
        r"""
        Line diff assertion. Fail if at least one difference found.

        .. code-block:: python

            text1 = 'a  b  c\nd\n'
            text2 = 'a b c\nd\t\n'
            result.diff(text1, text2, ignore_space_change=True)

        :param first: The first piece of textual content to be compared.
        :type first: ``str`` or ``list``
        :param second: The second piece of textual content to be compared.
        :type second: ``str`` or ``list``
        :param ignore_space_change: Ignore changes in the amount of whitespace.
        :type ignore_space_change: ``bool``
        :param ignore_whitespaces: Ignore all white space.
        :type ignore_whitespaces: ``bool``
        :param ignore_blank_lines: Ignore changes whose lines are all blank.
        :type ignore_blank_lines: ``bool``
        :param unified: If truth value, output differences in unified context.
                        Use an integer to specify the number of lines of
                        leading context before matching lines and trailing
                        context after matching lines. Defaults to 3.
        :type unified: ``bool`` or ``int``
        :param context: If truth value, output differences in copied context.
                        Use an integer to specify the number of lines of
                        leading context before matching lines and trailing
                        context after matching lines. Defaults to 3.
        :type context: ``bool`` or ``int``
        :return: Assertion pass status
        :rtype: ``bool``
        """
        entry = assertions.LineDiff(
            first,
            second,
            ignore_space_change=ignore_space_change,
            ignore_whitespaces=ignore_whitespaces,
            ignore_blank_lines=ignore_blank_lines,
            unified=unified,
            context=context,
            description=description,
            category=category,
        )

        return entry

    @assertion
    def graph(
        self,
        graph_type,
        graph_data,
        description,
        series_options,
        graph_options,
    ):
        """
        Displays a Graph in the report.

        .. code-block:: python

            result.graph('Line',
                      {
                          'graph 1':[{'x': 0, 'y': 8},{'x': 1, 'y': 5}]
                      },
                      description='Line Graph',
                      series_options={'graph 1':{"colour": "red"}},
                      graph_options=None)

        :param graph_type: Type of graph user wants to create.
                          Currently implemented:
                          'Line', 'Scatter', 'Bar', 'Hexbin',
                          'Pie', 'Whisker', 'Contour'
        :type graph_type: ``str``
        :param graph_data: Data to plot on the graph, for each series.
        :type graph_data: ``dict[str, list]``
        :param description: Text description for the graph.
        :type description: ``str``
        :param series_options: Customisation parameters for each
                               individual series.
                               Currently implemented:
                               1){'Colour': ``str``} - colour of that series
                               (str can be either basic colour name or RGB)
        :type series_options: ``dict[str, dict[str, object]]```.
        :param graph_options: Customisation parameters for overall graph
                              Currently implemented:
                               1){'xAxisTitle': ``str``} - x axis graph title
                               2){'yAxisTitle': ``str``} - y axis graph title
                               3){'legend': ``bool``} - to display legend
                               legend (Default: false)
        :type graph_options: ``dict[str, object]``.
        """
        entry = base.Graph(
            graph_type=graph_type,
            graph_data=graph_data,
            description=description,
            series_options=series_options,
            graph_options=graph_options,
        )

        return entry

    @assertion
    def attach(
        self, path, description=None, ignore=None, only=None, recursive=False
    ):
        """
        Attaches a file to the report.

        :param path: Path to the file or directory be to attached.
        :type path: ``str``
        :param description: Text description for the assertion.
        :type description: ``str``
        :param ignore: List of patterns of file name to ignore when
            attaching a directory.
        :type ignore: ``list`` or ``NoneType``
        :param only: List of patterns of file name to include when
            attaching a directory.
        :type only: ``list`` or ``NoneType``
        :param recursive: Recursively traverse sub-directories and attach
            all files, default is to only attach files in top directory.
        :type recursive: ``bool``
        :return: Always returns True, this is not an assertion so it cannot
                 fail.
        :rtype: ``bool``
        """
        if os.path.isfile(path):
            attachment = base.Attachment(
                path, description, scratch_path=self._scratch
            )
            self.attachments.append(attachment)
            return attachment
        elif os.path.isdir(path):
            directory = base.Directory(
                path,
                description,
                ignore=ignore,
                only=only,
                recursive=recursive,
                scratch_path=self._scratch,
            )
            for file in directory.file_list:
                filepath = os.path.join(directory.source_path, file)
                dst_path = os.path.join(directory.dst_path, file)
                if IS_WIN:
                    dst_path = dst_path.replace("\\", "/")
                self.attachments.append(
                    base.Attachment(
                        filepath=filepath,
                        description=None,
                        dst_path=dst_path,
                        scratch_path=None,
                    )
                )
            return directory
        else:
            raise FileNotFoundError(f"Path {path} not exist")

    @assertion
    def matplot(self, pyplot, width=None, height=None, description=None):
        """
        Displays a Matplotlib plot in the report.

        :param pyplot: Matplotlib pyplot object to be displayed.
        :type pyplot: ``matplotlib.pyplot``
        :param width: Figure width in inches, use pyplot defaul if not specified
        :type width: ``int``
        :param height: Figure height in inches, use pyplot default if not specified
        :type height: ``int``
        :param description: Text description for the assertion.
        :type description: ``str``
        :return: Always returns True, this is not an assertion so it cannot
                 fail.
        :rtype: ``bool``
        """
        filename = "{0}.png".format(strings.uuid4())
        image_file_path = os.path.join(self._scratch, filename)
        matplot = base.MatPlot(
            pyplot=pyplot,
            image_file_path=image_file_path,
            width=width,
            height=height,
            description=description,
        )
        self.attachments.append(matplot)

        return matplot

    @assertion
    def plotly(self, fig, description=None, style=None):
        filename = "{0}.json".format(strings.uuid4())
        data_file_path = os.path.join(self._scratch, filename)
        chart = base.Plotly(
            fig,
            data_file_path=data_file_path,
            style=style,
            description=description,
        )
        self.attachments.append(chart)

        return chart

    @property
    def serialized_entries(self):
        """
        Return entry data in dictionary form. This will then be stored
        in related ``TestCaseReport``'s ``entries`` attribute.
        """
        return [schema_registry.serialize(entry) for entry in self]

    def skip(self, reason: str, description: Optional[str] = None):
        """
        Skip a testcase with the given reason.

        :param reason: The message to show the user as reason for the skip.
        :type reason: ``str``
        :param description:  Text description for the assertion.
        :type description: ``str``
        """
        self.log(reason, description)
        raise SkipTestcaseException(reason)

    def __repr__(self):
        return repr(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __bool__(self):
        return True
