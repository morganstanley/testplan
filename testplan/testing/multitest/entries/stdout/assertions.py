"""Loggers for assertion objects"""
import os
import pprint
import re

from terminaltables import AsciiTable

import testplan.common.exporters.constants as constants
from testplan.common.exporters.pdf import format_cell_data
from testplan.common.utils.strings import Color, map_to_str

from .. import assertions
from .base import BaseRenderer, registry


@registry.bind_default(category="assertion")
class AssertionRenderer(BaseRenderer):
    """
    Default assertion logger. Renders simple details (file & line no),
    and assertion name/description and pass/fail status as header.
    """

    def pass_label(self, entry):
        return Color.green("Pass") if entry else Color.red("Fail")

    def get_assertion_details(self, entry):
        return None

    def get_details(self, entry):
        """
        Return file & line no (failing entries only), along
        with the extra info returned by `get_assertion_details`.
        """
        # pylint: disable=assignment-from-none
        assertion_details = self.get_assertion_details(entry)
        # pylint: enable=assignment-from-none

        if not entry:
            details = "File: {}".format(entry.file_path)
            details += os.linesep + "Line: {}".format(entry.line_no)
            if assertion_details:
                details += os.linesep + assertion_details
            return details
        return assertion_details

    def get_header(self, entry):
        return "{} - {}".format(
            self.get_header_text(entry), self.pass_label(entry)
        )


@registry.bind(
    assertions.Equal,
    assertions.NotEqual,
    assertions.Less,
    assertions.LessEqual,
    assertions.Greater,
    assertions.GreaterEqual,
)
class FunctionAssertionRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """
        Use a format like `1 == 2`, highlighting
        failing comparisons in red.
        """
        msg = "{} {} {}".format(entry.first, entry.label, entry.second)
        return msg if entry else Color.red(msg)


@registry.bind(assertions.IsClose)
class ApproximateEqualityAssertionRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """
        Use a format like `99 ~= 100 (with rel_tol=0.1, abs_tol=0.0)`,
        highlighting failing comparisons in red.
        """
        msg = "{} {} {} (rel_tol: {}, abs_tol: {})".format(
            entry.first,
            entry.label,
            entry.second,
            entry.rel_tol,
            entry.abs_tol,
        )
        return msg if entry else Color.red(msg)


@registry.bind(assertions.RegexMatch, assertions.RegexSearch)
class RegexMatchRenderer(AssertionRenderer):

    highlight_color = "green"

    def get_assertion_details(self, entry):
        """
        Return highlighted patterns within the string, if there is a match.
        Note that pattern & string (despite the name) could be bytes
        """

        string = entry.string
        pattern = "Pattern: `{}`{}".format(entry.pattern, os.linesep)

        if entry.match_indexes:
            curr_idx = 0
            parts = []

            for begin, end in entry.match_indexes:
                if begin > curr_idx:
                    parts.append(map_to_str(string[curr_idx:begin]))

                parts.append(
                    Color.colored(string[begin:end], self.highlight_color)
                )
                curr_idx = end

            if curr_idx < len(string):
                parts.append(string[curr_idx:])
            return "{}{}".format(pattern, "".join(parts))
        else:
            return "{}{}".format(pattern, string)


@registry.bind(assertions.RegexFindIter)
class RegexFindIterRenderer(RegexMatchRenderer):
    def get_assertion_details(self, entry):
        """Render `condition` attribute as well, if it exists"""
        msg = super(RegexFindIterRenderer, self).get_assertion_details(entry)
        if entry.condition_match is not None:
            msg += "{}Condition: {}".format(
                os.linesep,
                Color.colored(
                    entry.condition,
                    color="green" if entry.condition_match else "red",
                ),
            )
        return msg


@registry.bind(assertions.RegexMatchLine)
class RegexMatchLineRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """
        `RegexMatchLine` returns line indexes
        along with begin/end character indexes per matched line.
        Note: pattern & string (despite the name) could be bytes
        """
        pattern = "Pattern: `{}`{}".format(entry.pattern, os.linesep)
        if entry.match_indexes:
            parts = []
            match_map = {
                line_no: (begin, end)
                for line_no, begin, end in entry.match_indexes
            }

            for idx, line in enumerate(entry.lines):
                if idx in match_map:
                    begin, end = match_map[idx]
                    parts.append(
                        line[:begin]
                        + Color.green(line[begin:end])
                        + line[end:]
                    )
                else:
                    parts.append(line)
            return "{}{}".format(pattern, os.linesep.join(parts))
        return "{}{}".format(pattern, entry.string)


@registry.bind(assertions.RegexMatchNotExists, assertions.RegexSearchNotExists)
class RegexNotMatchRenderer(RegexMatchRenderer):
    highlight_color = "red"


@registry.bind(assertions.Contain, assertions.NotContain)
class MembershipRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """Return the member and container representations"""
        op_label = (
            "not in" if isinstance(entry, assertions.NotContain) else "in"
        )
        return "{} {} {}".format(entry.member, op_label, entry.container)


@registry.bind(assertions.TableMatch, assertions.TableDiff)
class TableMatchRenderer(AssertionRenderer):
    """
    Renders tabular data in ASCII table format

    Sample output:

      +----------+----------------+
      | age      | name           |
      +----------+----------------+
      | 32 == 32 | Bob == Bob     |
      | 24 == 24 | Susan == Susan |
      | 67 == 67 | Rick != David  |
      +----------+----------------+
    """

    def get_row_data(
        self,
        row_comparison,
        columns,
        include_columns=None,
        exclude_columns=None,
        display_index=False,
    ):
        """Return single row data to be printed"""

        def fmt(val):
            return val if val is not None else ""

        result = []

        for idx, column in enumerate(columns):
            actual = row_comparison.data[idx]
            other, matched = row_comparison.get_comparison_value(column, idx)

            value_limit = int((constants.CELL_STRING_LENGTH - 4) / 2)
            other, actual = format_cell_data(
                data=[other, actual], limit=value_limit
            )

            include_columns = include_columns or columns
            exclude_columns = exclude_columns or []

            if (
                (column not in include_columns)
                or (column in exclude_columns)
                or matched is None
            ):
                result.append(f"{fmt(actual)} .. {fmt(other)}")
            elif matched:
                result.append(Color.green(f"{fmt(actual)} == {fmt(other)}"))
            else:
                result.append(Color.red(f"{fmt(actual)} != {fmt(other)}"))

        if display_index:
            result = [row_comparison.idx] + result
        return result

    def get_assertion_details(self, entry):
        """Return row by row match results in tabular format"""
        if entry.message:
            result = (
                Color.red(entry.message) if not entry.passed else entry.message
            )
        else:
            result = ""

        row_data = [
            self.get_row_data(
                row_comparison,
                entry.display_columns,
                display_index=entry.report_fails_only,
            )
            for row_comparison in entry.data
        ]

        columns = (
            ["row"] + list(entry.display_columns)
            if entry.report_fails_only
            else entry.display_columns
        )
        ascii_table = (
            AsciiTable([columns] + row_data).table if row_data else ""
        )

        return "{}{}{}".format(
            result, os.linesep if result and ascii_table else "", ascii_table
        )


@registry.bind(assertions.ColumnContain)
class ColumnContainRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):

        ascii_columns = [entry.column, "Passed"]
        if entry.report_fails_only:
            ascii_columns = ["row"] + ascii_columns

        table = []
        for comp_obj in entry.data:
            ascii_row = [comp_obj.value, Color.passed(check=comp_obj.passed)]
            if entry.report_fails_only:
                ascii_row = [comp_obj.idx] + ascii_row
            table.append(ascii_row)

        return "{}{}{}".format(
            "Values: {}".format(entry.values),
            os.linesep,
            AsciiTable([ascii_columns] + table).table,
        )


def add_printable_dict_comparison(result, row):
    """Stdout representation of fix/dict match rows."""
    indent, key, status, left, right = row
    if left or right:
        if not left:
            left = "None"
        if not right:
            right = "None"
    else:
        left = ""
        right = ""

    if status == "Passed":
        coloured = Color.colored(status, "green")
        operator = " == "
    elif status == "Failed":
        coloured = Color.colored(status, "red")
        operator = " != "
    else:
        coloured = "Ignore"
        operator = "    "

    result.append(
        "{}  {}{}    {}{}{}".format(
            "({})".format(coloured) if coloured else " " * len("(Passed)"),
            " " * 4 * indent,
            "Key({}),".format(key) if key else "",
            "{} <{}>".format(left[1], left[0])
            if isinstance(left, tuple)
            else left,
            operator if left and right else " ",
            "{} <{}>".format(right[1], right[0])
            if isinstance(right, tuple)
            else right,
        )
    )


@registry.bind(assertions.DictMatch, assertions.FixMatch)
class DictMatchRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """Return fix and dict match result representations"""
        result = []
        for row in entry.comparison:
            add_printable_dict_comparison(result, row)
        if result:
            result.append("")
        return str(os.linesep.join(result))


@registry.bind(assertions.DictCheck, assertions.FixCheck)
class DictCheckRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """Return `has_keys` & `absent_keys` context"""
        msg = ""
        if entry.has_keys:
            msg += "Existence check: {}".format(entry.has_keys)
            if entry.has_keys_diff:
                msg += "{}\tMissing keys: {}".format(
                    os.linesep, Color.red(list(entry.has_keys_diff))
                )
        if entry.absent_keys:
            if msg:
                msg += os.linesep
            msg += "Absence check: {}".format(entry.absent_keys)
            if entry.absent_keys_diff:
                msg += "{}\tKey should be absent: {}".format(
                    os.linesep, Color.red(list(entry.absent_keys_diff))
                )

        return msg


@registry.bind(assertions.DictMatchAll, assertions.FixMatchAll)
class DictMatchAllRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):
        """Return fix and dict match_all result representations"""

        result = []
        for match in entry.matches:
            comparison = match["comparison"]
            description = match["description"]
            passed = match["passed"]
            if passed is True:
                coloured = Color.colored("Passed", "green")
            else:
                coloured = Color.colored("Failed", "red")
            result.append("({}) {}".format(coloured, description))
            for row in comparison:
                add_printable_dict_comparison(result, row)
            if result:
                result.append("")
        return str(os.linesep.join(result))


@registry.bind(assertions.ExceptionRaised, assertions.ExceptionNotRaised)
class ExceptionRaisedRenderer(AssertionRenderer):
    def get_assertion_details(self, entry):

        raised_exc = entry.raised_exception
        expected_exceptions = ", ".join(
            [exc.__name__ for exc in entry.expected_exceptions]
        )

        label = (
            "not instance of"
            if isinstance(entry, assertions.ExceptionNotRaised)
            else "instance of"
        )

        msg = "{} {} {}".format(type(raised_exc), label, expected_exceptions)

        if entry.func:
            msg += "{} Function: {}".format(
                os.linesep,
                str(entry.func)
                if entry.passed
                else Color.red(str(entry.func)),
            )

        if entry.pattern:
            msg += "{} Pattern: {}".format(
                os.linesep,
                entry.pattern if entry.passed else Color.red(entry.pattern),
            )

            msg += "{} Exception message: {}".format(
                os.linesep, entry.raised_exception
            )

        return msg


@registry.bind(assertions.XMLCheck)
class XMLCheckRenderer(AssertionRenderer):
    """Renderer for XMLCheck"""

    def get_assertion_details(self, entry):
        """
        Render the message if there is any, then render XMLTagComparison items.
        """
        result = []

        result.append("xpath: {}".format(entry.xpath))

        if entry.namespaces:
            result.append("Namespaces: {}".format(entry.namespaces))

        if entry.message:
            result.append(
                entry.message if entry.passed else Color.red(entry.message)
            )

        if entry.data:
            result.append("Tags:")

        for tag_comp in entry.data:
            template = "  {actual} {operator} {expected}"
            common = dict(
                actual=tag_comp.tag, expected=tag_comp.comparison_value
            )

            if tag_comp.passed:
                result.append(template.format(operator="==", **common))
            else:
                result.append(
                    Color.red(template.format(operator="!=", **common))
                )
        return os.linesep.join(result)


@registry.bind(assertions.Fail)
class FailRenderer(AssertionRenderer):
    def get_header(self, entry):
        return Color.red(entry.description)

    def get_assertion_details(self, entry):
        if isinstance(entry.message, str):
            if entry.description:
                return Color.red(str(entry.message))
            else:
                return None
        else:
            return pprint.pformat(entry.message)


@registry.bind(assertions.EqualSlices)
class EqualSlicesRenderer(AssertionRenderer):
    """
    Display slice, comparison indexes, mismatch
    indexes, actual and expected iterables.

    Sample output:

        Equal Slices - Pass
          slice(2, 4, None)
            Actual:    [3, 4]
            Expected:  [3, 4]
          slice(5, 7, None)
            Actual:    ['d', 'e']
            Expected:  [6, 7]
    """

    def get_assertion_details(self, entry):
        result = []

        for slice_comp in entry.data:
            result.append(
                "{}".format(
                    slice_comp.slice
                    if slice_comp.passed
                    else Color.red(slice_comp.slice)
                )
            )

            # Display mismatched indexes if slice has
            # a step, for easier debugging
            if slice_comp.mismatch_indices:
                result.append(
                    "  Mismatched indices: {}".format(
                        slice_comp.mismatch_indices
                    )
                )
            result.append("  Actual:\t{}".format(slice_comp.actual))
            result.append("  Expected:\t{}".format(slice_comp.expected))

        return os.linesep.join(result)


@registry.bind(assertions.EqualExcludeSlices)
class EqualExcludeSlicesRenderer(AssertionRenderer):
    """
    Display excluded indexes, compared indexes, actual and expected iterables.
    """

    def get_assertion_details(self, entry):
        result = [
            "{} - excluded".format(slice_comp.slice)
            for slice_comp in entry.data
        ]

        actual = [entry.actual[i] for i in entry.included_indices]
        expected = [entry.expected[i] for i in entry.included_indices]
        result.extend(
            [
                "{}: {}".format(
                    title, data if entry.passed else Color.red(data)
                )
                for title, data in (
                    ("Compared indices", list(entry.included_indices)),
                    ("Actual", actual),
                    ("Expected", expected),
                )
            ]
        )

        return os.linesep.join(result)


@registry.bind(assertions.LineDiff)
class LineDiffRenderer(AssertionRenderer):
    """
    Display 2 blocks of textual content, truncate them if too long, also
    display the difference between them if found.
    """

    def get_assertion_details(self, entry):
        result = []

        if not entry.passed:
            result.append(Color.red("*** a.text ***" + os.linesep))
            for line in self._get_truncated_lines(
                entry.first, n=constants.NUM_DISPLAYED_ROWS
            ):
                result.append("  {}".format(line))
            if not (result[-1].endswith(os.linesep) or result[-1][-1] == "\n"):
                result[-1] += os.linesep

            result.append(Color.red("*** b.text ***" + os.linesep))
            for line in self._get_truncated_lines(
                entry.second, n=constants.NUM_DISPLAYED_ROWS
            ):
                result.append("  {}".format(line))
            if not (result[-1].endswith(os.linesep) or result[-1][-1] == "\n"):
                result[-1] += os.linesep

        options = ""
        options += "-b " if entry.ignore_space_change else ""
        options += "-w " if entry.ignore_whitespaces else ""
        options += "-B " if entry.ignore_blank_lines else ""
        options += "-u " if entry.unified else ""
        options += "-c " if entry.context and not entry.unified else ""
        options = " ( " + options + ")" if options else ""

        if entry.passed:
            result.append("No difference found{}".format(options))
        else:
            result.append(
                Color.red("Differences{}:{}".format(options, os.linesep))
            )
            for line in self._get_truncated_lines(
                entry.delta, n=constants.NUM_DISPLAYED_ROWS * 5
            ):
                result.append("  {}".format(line))
            result[-1] = re.sub(r"[\r\n]+$", "", result[-1])

        return "".join(result)

    def _get_truncated_lines(self, lines, n=0):
        # At most keep n lines, n==0 means no truncation.
        for i, line in enumerate(lines):
            if n > 0 and i >= n:
                yield "[truncated after displaying first %d lines ...]" % n
                break
            yield line
