"""
Classes that parse command-line arguments used to control testplan behaviour.
This module encodes the argument and option names, types and behaviours.
"""
import argparse
import copy
import os
import random
import sys

from testplan.common.utils import logger
from testplan import defaults
from testplan.report.testing import styles, ReportTagsAction
from testplan.testing import listing, filtering, ordering


class HelpParser(argparse.ArgumentParser):
    """
    HelpParser extends ``ArgumentParser`` in order to print the help message
    when parsing fails.
    """

    def error(self, message):
        """
        Override error method to print error and then display help message

        :param message: The parsing error message
        :type message: ``str``
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


class TestplanParser(object):
    """
    Wrapper around `argparse.ArgumentParser`, adds extra step for processing
    arguments, esp. if they are dependent on each other.
    """

    def __init__(self, name, default_options):
        self.cmd_line = copy.copy(sys.argv)
        self.name = name
        self._default_options = default_options

    def add_arguments(self, parser):
        """Virtual method to be overridden by custom parsers."""
        pass

    def generate_parser(self):
        """Generate an argparse.Argument parser instance."""
        epilog = ""
        parser = HelpParser(
            "Test Plan ({})".format(self.name),
            epilog,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument(
            "--list",
            action="store_true",
            default=False,
            help="Shortcut for `--info name`.",
        )

        parser.add_argument(
            "--info",
            dest="test_lister",
            metavar="TEST_INFO",
            **listing.listing_registry.to_arg().get_parser_context(
                default=self._default_options["test_lister"]
            )
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
            "processes, default to 14400s(4h), set to 0 to disable.",
        )

        general_group.add_argument(
            "-i",
            "--interactive",
            dest="interactive_port",
            nargs="?",
            default=self._default_options["interactive_port"],
            const=defaults.WEB_SERVER_PORT,
            type=int,
            help="Enable interactive mode. A port may be specified, otherwise "
            "the port defaults to {}.".format(defaults.WEB_SERVER_PORT),
        )

        filter_group = parser.add_argument_group("Filtering")

        filter_group.add_argument(
            "--patterns",
            action=filtering.PatternAction,
            default=[],
            nargs="+",
            metavar="TEST_FILTER",
            type=str,
            help="""\
Test filter, supports glob notation & multiple arguments.

--pattern <Multitest Name>
--pattern <Multitest Name 1> <Multitest Name 2>
--pattern <Multitest Name 1> --pattern <Multitest Name 2>
--pattern <Multitest Name>:<Suite Name>
--pattern <Multitest Name>:<Suite Name>:<Testcase name>
--pattern <Multitest Name>:*:<Testcase name>
--pattern *:<Suite Name>:<Testcase name>""",
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
            help="Enable verbose mode that will also set the stdout-style "
            'option to "detailed".',
        )

        report_group.add_argument(
            "-d",
            "--debug",
            action="store_true",
            default=self._default_options["debug"],
            help="Enable debug mode.",
        )

        report_group.add_argument(
            "-b",
            "--browse",
            action="store_true",
            default=self._default_options["browse"],
            help="Automatically open report to browse. Must be specified "
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
            help="Start the web server to view the Testplan UI. A port can be "
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
            help="Specify log level for file logs. Set to None to disable "
            "file logging.",
        )

        self.add_arguments(parser)
        return parser

    def parse_args(self):
        """
        Generate the parser & return parsed command line args.
        """
        return self.generate_parser().parse_args()

    def process_args(self, namespace):
        """
        Override this method to add extra argument processing logic.

        Can be used for interdependent argument processing.

        Testplan will use the result dictionary
        to initialize the configuration.
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

        if args["interactive_port"] is not None:
            args["auto_report_uid"] = False

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
