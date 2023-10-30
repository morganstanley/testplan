"""
Classes that parse command-line arguments used to control testplan behaviour.
This module encodes the argument and option names, types, and behaviours.
"""
import argparse
import copy
import json
import sys
import warnings
from typing import Dict, List

import schema

from testplan import defaults
from testplan.common.utils import logger
from testplan.report.testing import (
    ReportFilterAction,
    ReportTagsAction,
    styles,
)
from testplan.testing import filtering, listing, ordering


class HelpParser(argparse.ArgumentParser):
    """
    Extends ``ArgumentParser`` in order to print the help message upon failure.
    """

    def error(self, message: str) -> None:
        """
        Overrides `error` method to print error and display help message.

        :param message: the parsing error message
        """
        error_header = "=" * 30 + " ERROR " + "=" * 30
        error_ctx = [
            "\n",
            error_header,
            "\n",
            "\n",
            message,
            "\n",
            "=" * len(error_header),
            "\n",
        ]

        self.print_help()
        sys.stderr.writelines(error_ctx)
        sys.exit(2)


class TestplanParser:
    """
    Wrapper around `argparse.ArgumentParser`, adds extra step for processing
    arguments, useful when there are cross-dependencies between them.
    """

    def __init__(self, name: str, default_options: Dict) -> None:
        self.cmd_line = copy.copy(sys.argv)
        self.name = name
        self._default_options = default_options

    def add_arguments(self, parser):
        """
        Virtual method to be overridden by custom parsers.

        :param parser: parser instance
        """
        pass

    def generate_parser(self) -> HelpParser:
        """Generates an `argparse.ArgumentParser` instance."""
        epilog = ""
        parser = HelpParser(
            "Test Plan ({})".format(self.name),
            epilog,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument(
            "--info",
            dest="test_lister",
            metavar="TEST_INFO",
            **listing.listing_registry.to_arg().get_parser_context(
                default=self._default_options["test_lister"]
            )
        )

        parser.add_argument(
            "--list",
            action="store_true",
            default=False,
            help="Shortcut for `--info name`.",
        )

        general_group = parser.add_argument_group("General")

        general_group.add_argument(
            "--runpath",
            type=str,
            metavar="PATH",
            default=self._default_options["runpath"],
            help="Path under which all temp files and logs will be created.",
        )

        general_group.add_argument(
            "--timeout",
            metavar="TIMEOUT",
            default=self._default_options["timeout"],
            type=int,
            help="Timeout value in seconds to kill Testplan and all child "
            "processes. Defaults to 14400s (4h). Set to 0 to disable.",
        )

        general_group.add_argument(
            "-i",
            "--interactive",
            dest="interactive_port",
            nargs="?",
            default=self._default_options["interactive_port"],
            const=defaults.WEB_SERVER_PORT,
            type=int,
            help="Enables interactive mode. A port may be specified, otherwise"
            " the port defaults to {}.".format(defaults.WEB_SERVER_PORT),
        )

        general_group.add_argument(
            "--pre-start-environments",
            dest="pre_start_environments",
            type=str,
            default=None,
            nargs="*",
            help="Enables pre-start of environments corresponding to the "
            "MultiTest names passed. Defaults to no environment pre-started.",
        )

        general_group.add_argument(
            "--trace-tests",
            metavar="PATH",
            type=_read_json_file,
            dest="tracing_tests",
            help="Enable the tracing tests feature. A JSON file containing "
            "file names and line numbers to be watched by the tracer must be "
            "specified.",
        )

        general_group.add_argument(
            "--trace-tests-output",
            metavar="PATH",
            default="-",
            type=str,
            dest="tracing_tests_output",
            help="Specify output file for tests impacted by change in "
            'Testplan pattern format (see "--trace-tests"). Will be ignored '
            'if "--trace-tests" is not specified. Default to standard output.',
        )

        general_group.add_argument(
            "--xfail-tests",
            metavar="PATH",
            type=_read_json_file,
            help="""
Read a list of testcase name patterns from a JSON files, and mark matching testcases as xfail.
This feature works for MultiTest, GTest and CPPUnit.
A typical input JSON looks like below:
{
    "Fatal GTest:*:*": {
        "reason": "test known to crash",
        "strict": true
    },
    "Flaky GTest:SuiteName:CaseName": {
        "reason": "test not stable",
        "strict": false
    },
    "Fatal MultiTest:*:*": {
        "reason": "env does not start",
        "strict": true
    },
    "Flaky MultiTest:Suite Name:*": {
        "reason": "everything under that suite flaky",
        "strict": true
    }
}

"with each entry looks like: "
'{"<Multitest>:<TestSuite>:<testcase>": '
'{"reason": <value>, "strict": <value>} }',
""",
        )

        general_group.add_argument(
            "--runtime-data",
            metavar="PATH",
            type=_runtime_json_file,
            help="Historical runtime data which will be used for Multitest "
            "auto-part and weight-based Task smart-scheduling with "
            "entries looks like: "
            """
{
    "<Multitest>": {
        "execution_time": 199.99,
        "setup_time": 39.99,
    },
    ......
}""",
        )

        filter_group = parser.add_argument_group("Filtering")

        filter_pattern_group = filter_group.add_mutually_exclusive_group()

        filter_pattern_group.add_argument(
            "--patterns",
            action=filtering.PatternAction,
            default=[],
            nargs="+",
            metavar="TEST_FILTER",
            type=str,
            help="""\
Test filter, supports glob notation & multiple arguments.

--patterns <Multitest Name>
--patterns <Multitest Name 1> <Multitest Name 2>
--patterns <Multitest Name 1> --patterns <Multitest Name 2>
--patterns <Multitest Name>:<Suite Name>
--patterns <Multitest Name>:<Suite Name>:<Testcase name>
--patterns <Multitest Name>:*:<Testcase name>
--patterns *:<Suite Name>:<Testcase name>""",
        )

        # NOTE: custom type is applied before custom action
        filter_pattern_group.add_argument(
            "--patterns-file",
            metavar="FILE",
            dest="patterns",
            type=_read_text_file,
            action=filtering.PatternAction,
            help="""\
Test filter supplied in a file, with one pattern per line.

--patterns-file <File>
""",
        )

        filter_group.add_argument(
            "--tags",
            action=filtering.TagsAction,
            default=[],
            nargs="+",
            metavar="TEST_FILTER",
            help="""\
Test filter, runs tests that match ANY of the given tags.

--tags <tag_name_1> --tags <tag_name 2>
--tags <tag_name_1> <tag_category_1>=<tag_name_2>""",
        )

        filter_group.add_argument(
            "--tags-all",
            action=filtering.TagsAllAction,
            default=[],
            nargs="+",
            metavar="TEST_FILTER",
            help="""\
Test filter, runs tests that match ALL of the given tags.

--tags-all <tag_name_1> --tags <tag_name 2>
--tags-all <tag_name_1> <tag_category_1>=<tag_name_2>""",
        )

        ordering_group = parser.add_argument_group("Ordering")

        ordering_group.add_argument(
            "--shuffle",
            nargs="+",
            type=str,
            default=self._default_options["shuffle"],
            choices=[enm.value for enm in ordering.SortType],
            help="Shuffle execution order",
        )

        ordering_group.add_argument(
            "--shuffle-seed",
            metavar="SEED",
            type=float,
            default=self._default_options["shuffle_seed"],
            help="Seed shuffle with a specific value, useful to "
            "reproduce a particular order.",
        )

        report_group = parser.add_argument_group("Reporting")

        report_group.add_argument(
            "--stdout-style",
            **styles.StyleArg.get_parser_context(
                default=self._default_options["stdout_style"]
            )
        )

        report_filter_group = report_group.add_mutually_exclusive_group()
        report_filter_group.add_argument(
            "--report-filter",
            metavar="{E,F,I,P,S,U,X,A,B,C,...}",
            dest="reporting_filter",
            type=str,
            help="Only include testcases with execution result Error (E), "
            "Failed (F), Incomplete (I), Passed (P), Skipped (S), "
            "Unstable (U), Unknown (X), XFail (A), XPass (B) and "
            "XPass-Strict (C) in Testplan report. Use lower-case characters "
            'to exclude certain testcases from the report. Use "PS" will '
            'select passed and skipped testcases only, and use "ps" will '
            "select all the testcases that are not passed and not skipped. "
            "Note using upper-case and lower-case letters together is not "
            "allowed due to potential ambiguity.",
        )

        report_filter_group.add_argument(
            "--omit-passed",
            nargs=0,
            action=ReportFilterAction.use_filter("p"),
            help='Equivalent to "--report-filter=p", cannot be used with '
            '"--report-filter" together.',
        )

        report_filter_group.add_argument(
            "--omit-skipped",
            nargs=0,
            action=ReportFilterAction.use_filter("s"),
            help='Equivalent to "--report-filter=s", cannot be used with '
            '"--report-filter" together.',
        )

        report_group.add_argument(
            "--pdf",
            dest="pdf_path",
            default=self._default_options["pdf_path"],
            metavar="PATH",
            help="Path for PDF report.",
        )

        report_group.add_argument(
            "--json",
            dest="json_path",
            default=self._default_options["json_path"],
            metavar="PATH",
            help="Path for JSON report.",
        )

        report_group.add_argument(
            "--xml",
            dest="xml_dir",
            default=self._default_options["xml_dir"],
            metavar="DIRECTORY",
            help="Directory path for XML reports.",
        )

        report_group.add_argument(
            "--http",
            dest="http_url",
            default=self._default_options["http_url"],
            metavar="URL",
            help="Web URL for posting report.",
        )

        report_group.add_argument(
            "--report-dir",
            default=self._default_options["report_dir"],
            metavar="PATH",
            help="Target directory for tag filtered report output.",
        )

        report_group.add_argument(
            "--pdf-style",
            **styles.StyleArg.get_parser_context(
                default=self._default_options["pdf_style"]
            )
        )

        report_group.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=self._default_options["verbose"],
            help="Enables verbose mode that will also set the stdout-style "
            'option to "detailed".',
        )

        report_group.add_argument(
            "-d",
            "--debug",
            action="store_true",
            default=self._default_options["debug"],
            help="Enables debug mode.",
        )

        report_group.add_argument(
            "-b",
            "--browse",
            action="store_true",
            default=self._default_options["browse"],
            help="Automatically opens report to browse. Must be specified "
            'with "--ui" to open it locally, or upload it to a web server '
            "with a customized exporter which has a `report_url`, or there "
            "will be nothing to open.",
        )

        report_group.add_argument(
            "-u",
            "--ui",
            dest="ui_port",
            nargs="?",
            default=self._default_options["ui_port"],
            const=defaults.WEB_SERVER_PORT,
            type=int,
            help="Starts the web server for the Testplan UI. A port can be "
            "specified, otherwise defaults to {}. A JSON report will be "
            "saved locally.".format(self._default_options["ui_port"]),
        )

        report_group.add_argument(
            "--report-tags",
            nargs="+",
            action=ReportTagsAction,
            default=self._default_options["report_tags"],
            metavar="REPORT_FILTER",
            help="""\
Report filter, generates a separate report (PDF by default)
that match ANY of the given tags.

--report-tags <tag_name_1> --report-tags <tag_name 2>
--report-tags <tag_name_1> <tag_category_1>=<tag_name_2>""",
        )

        report_group.add_argument(
            "--report-tags-all",
            nargs="+",
            action=ReportTagsAction,
            default=self._default_options["report_tags_all"],
            metavar="REPORT_FILTER",
            help="""\
Report filter, generates a separate report (PDF by default)
that match ALL of the given tags.

--report-tags-all <tag_name_1> --report-tags-all <tag_name 2>
--report-tags-all <tag_name_1> <tag_category_1>=<tag_name_2>""",
        )

        report_group.add_argument(
            "--file-log-level",
            choices=LogLevelAction.LEVELS.keys(),
            default=self._default_options["file_log_level"],
            action=LogLevelAction,
            help="Specifies log level for file logs. Set to None to disable "
            "file logging.",
        )

        report_group.add_argument(
            "--label",
            default=self._default_options["label"],
            help="Labels the test report with the given name, "
            'useful to categorize or classify similar reports (aka "run-id").',
        )

        self.add_arguments(parser)
        return parser

    def parse_args(self):
        """
        Generates the parser & return parsed command line args.
        """
        return self.generate_parser().parse_args()

    def process_args(self, namespace: argparse.Namespace) -> Dict:
        """
        Overrides this method to add extra argument processing logic.

        Can be used for interdependent argument processing.

        Testplan uses the result dictionary to initialize the configuration.

        :param namespace: namespace of parsed arguments
        :return: initial configuration
        """
        args = dict(**vars(namespace))

        filter_args = filtering.parse_filter_args(
            parsed_args=args, arg_names=("tags", "tags_all", "patterns")
        )

        if filter_args:
            args["test_filter"] = filter_args

        # Cmdline supports shuffle ordering only for now
        if args.get("shuffle"):
            args["test_sorter"] = ordering.ShuffleSorter(
                seed=args["shuffle_seed"], shuffle_type=args["shuffle"]
            )

        # Set stdout style and logging level options according to
        # verbose/debug parameters. Debug output should be a superset of
        # verbose output, i.e. running with just "-d" should automatically
        # give you all "-v" output plus extra DEBUG logs.
        if args["verbose"] or args["debug"]:
            args["stdout_style"] = styles.Style(
                styles.StyleEnum.ASSERTION_DETAIL,
                styles.StyleEnum.ASSERTION_DETAIL,
            )
            if args["debug"]:
                args["logger_level"] = logger.DEBUG
            elif args["verbose"]:
                args["logger_level"] = logger.INFO

        if args["list"] and not args["test_lister"]:
            args["test_lister"] = listing.NameLister()

        if (
            args["interactive_port"] is not None
            and args["tracing_tests"] is not None
        ):
            warnings.warn(
                "Tracing tests feature not available in interactive mode."
            )
            args["tracing_tests"] = None

        return args


class LogLevelAction(argparse.Action):
    """
    Custom parser action to convert from a string log level to its int value,
    e.g. "DEBUG" -> 10. The level can also be specified as "NONE", which will
    be stored internally as None.
    """

    # Copy our logger levels but add a special-case value NONE to disable
    # file logging entirely.
    LEVELS = logger.TestplanLogger.LEVELS.copy()
    LEVELS["NONE"] = None

    def __call__(self, parser, namespace, values, option_string=None):
        """Store the log level value corresponding to the level's name."""
        setattr(namespace, self.dest, self.LEVELS[values])


def _read_json_file(file: str) -> dict:
    with open(file, "r") as fp:
        return json.load(fp)


def _read_text_file(file: str) -> List[str]:
    with open(file, "r") as fp:
        return fp.read().splitlines()


runtime_schema = schema.Schema(
    {
        str: {
            "execution_time": schema.Or(int, float),
            "setup_time": schema.Or(int, float),
        }
    }
)


def _runtime_json_file(file: str) -> dict:
    with open(file) as fp:
        runtime_info = json.load(fp)
        if runtime_schema.is_valid(runtime_info):
            return runtime_info
        raise RuntimeError("Unexpected runtime file format!")
