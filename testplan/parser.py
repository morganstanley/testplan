"""
Classes that parse command-line arguments used to control testplan behaviour.
This module encodes the argument and option names, types and behaviours.
"""
import argparse
import copy
import os
import random
import sys

from testplan import defaults
from testplan.common.config import DefaultValueWrapper, DEFAULT
from testplan.common.utils import logger
from testplan.report.testing import styles, ReportTagsAction
from testplan.testing import listing, filtering, ordering

USER_SPECIFIED_ARGS = '_user_specified_args'


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
        error_header = '=' * 30 + ' ERROR ' + '=' * 30
        error_ctx = [
            '\n', error_header, '\n',
            '\n', message, '\n',
            '=' * len(error_header), '\n'
        ]

        self.print_help()
        sys.stderr.writelines(error_ctx)
        sys.exit(2)


class TestplanParser(object):
    """
    Wrapper around `argparse.ArgumentParser`, adds extra step for processing
    arguments, esp. if they are dependent on each other.
    """
    def __init__(self, name):
        self.cmd_line = copy.copy(sys.argv)
        self.name = name

    def add_arguments(self, parser):
        """Virtual method to be overridden by custom parsers."""
        pass

    def generate_parser(self):
        """Generate an argparse.Argument parser instance."""
        epilog = ''
        parser = HelpParser(
            'Test Plan ({})'.format(self.name), epilog,
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser.add_argument(
            '--list', action='store_true',
            default=DEFAULT(False), help='Shortcut for `--info name`'
        )

        parser.add_argument(
            '--info', dest='test_lister', metavar='TEST_INFO',
            **listing.ListingArg.get_parser_context(
                default=DEFAULT(None, upper_end_preferred=True))
        )

        parser.add_argument(
            '-i', '--interactive', action='store_true', dest='interactive',
            default=DEFAULT(False), help='Enable interactive mode.'
        )

        general_group = parser.add_argument_group('General')
        general_group.add_argument(
            '--runpath', type=str, metavar='PATH',
            default=DEFAULT(None, upper_end_preferred=True),
            help='Path under which all temp files and logs will be created'
        )

        filter_group = parser.add_argument_group('Filtering')

        filter_group.add_argument(
            '--patterns', action=filtering.PatternAction,
            default=[], nargs='+', metavar='TEST_FILTER', type=str,
            help=os.linesep.join([
                'Test filter, supports glob notation & multiple arguments.',
                '',
                '--patterns <Multitest Name>',
                '--patterns <Multitest Name 1> <Multitest Name 2>',
                '--patterns <Multitest Name 1> --patterns <Multitest Name 2>',
                '--patterns <Multitest Name>:<Suite Name>',
                '--patterns <Multitest Name>:<Suite Name>:<Testcase name>',
                '--patterns <Multitest Name>:*:<Testcase name>',
                '--patterns *:<Suite Name>:<Testcase name>',
            ])
        )

        filter_group.add_argument(
            '--tags', action=filtering.TagsAction,
            default=[], nargs='+', metavar='TEST_FILTER',
            help=os.linesep.join([
                'Test filter, runs tests that match ANY of the given tags.',
                '',
                '--tags <tag_name_1> --tags <tag_name 2>',
                '--tags <tag_name_1> <tag_category_1>=<tag_name_2>',
            ])
        )

        filter_group.add_argument(
            '--tags-all', action=filtering.TagsAllAction,
            default=[], nargs='+', metavar='TEST_FILTER',
            help=os.linesep.join([
                'Test filter, runs tests that match ALL of the given tags.',
                '',
                '--tags-all <tag_name_1> --tags <tag_name 2>',
                '--tags-all <tag_name_1> <tag_category_1>=<tag_name_2>',
            ])
        )

        ordering_group = parser.add_argument_group('Ordering')

        ordering_group.add_argument(
            '--shuffle', nargs='+', type=str, default=DEFAULT([]),
            choices=[enm.value for enm in ordering.SortType],
            help='Shuffle execution order'
        )

        ordering_group.add_argument(
            '--shuffle-seed', metavar='SEED', type=float,
            default=DEFAULT(float(random.randint(1, 9999))),
            help='Seed shuffle with a specific value, useful to '
                 'reproduce a particular order.'
        )

        report_group = parser.add_argument_group('Reporting')

        report_group.add_argument(
            '--stdout-style',
            **styles.StyleArg.get_parser_context(
                default=DEFAULT('summary', upper_end_preferred=True))
        )

        report_group.add_argument(
            '--pdf', dest='pdf_path', metavar='PATH',
            default=DEFAULT(None, upper_end_preferred=True),
            help='Path for PDF report.'
        )

        report_group.add_argument(
            '--json', dest='json_path', metavar='PATH',
            default=DEFAULT(None, upper_end_preferred=True),
            help='Path for JSON report.'
        )

        report_group.add_argument(
            '--xml', dest='xml_dir', metavar='DIRECTORY',
            default=DEFAULT(None, upper_end_preferred=True),
            help='Directory path for XML reports.'
        )

        report_group.add_argument(
            '--report-dir', metavar='DIRECTORY',
            default=DEFAULT(defaults.REPORT_DIR, upper_end_preferred=True),
            help='Target directory for tag filtered report output.'
        )

        report_group.add_argument(
            '--pdf-style',
            **styles.StyleArg.get_parser_context(
                default=DEFAULT('extended-summary', upper_end_preferred=True))
        )

        report_group.add_argument(
            '-v', '--verbose', action='store_true', dest='verbose',
            default=DEFAULT(False),
            help='Enable verbose mode that will also set the stdout-style '
                 'option to "detailed".')

        report_group.add_argument(
            '-d', '--debug', action='store_true', dest='debug',
            default=DEFAULT(False),
            help='Enable debug mode.')

        report_group.add_argument(
            '-b', '--browse', action='store_true', dest='browse',
            default=DEFAULT(False),
            help=('Automatically open report to browse. Must be specifed with '
                  '"--pdf" or "--json --ui" or there will be nothing to open.'))

        report_group.add_argument(
            '-u', '--ui', dest='ui_port', nargs='?',
            const=DEFAULT(defaults.WEB_SERVER_PORT), type=int,
            default=DEFAULT(None),
            help=('Start the web server to view the Testplan UI. A port can be '
                  'specified, otherwise defaults to {}. A JSON report will be '
                  'saved locally.').format(defaults.WEB_SERVER_PORT))

        report_group.add_argument(
            '--report-tags', nargs='+',
            action=ReportTagsAction, metavar='REPORT_FILTER',
            default=DEFAULT([], upper_end_preferred=True),
            help=os.linesep.join([
                'Report filter, generates a separate report (PDF by default)',
                'that match ANY of the given tags.',
                '',
                '--report-tags <tag_name_1> --report-tags <tag_name 2>',
                '--report-tags <tag_name_1> <tag_category_1>=<tag_name_2>',
            ])
        )

        report_group.add_argument(
            '--report-tags-all', nargs='+',
            action=ReportTagsAction, metavar='REPORT_FILTER',
            default=DEFAULT([], upper_end_preferred=True),
            help=os.linesep.join([
                'Report filter, generates a separate report (PDF by default)',
                'that match ALL of the given tags.',
                '',
                '--report-tags-all <tag_name_1> --report-tags-all <tag_name 2>',
                '--report-tags-all <tag_name_1> <tag_category_1>=<tag_name_2>',
            ])
        )

        report_group.add_argument(
            '--file-log-level',
            action=LogLevelAction,
            choices=LogLevelAction.LEVELS.keys(),
            default=DEFAULT(logger.DEBUG),
            help='Specify log level for file logs. Set to NONE to disable file '
                 'logging.')

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
        cmd_line_args = args.setdefault(USER_SPECIFIED_ARGS, set())
        cmd_line_args.update({
            key for key, value in args.items()
            if not isinstance(value, DefaultValueWrapper)
        })

        filter_args = filtering.parse_filter_args(
            parsed_args=args,
            arg_names=('tags', 'tags_all', 'patterns'))

        if filter_args:
            args['test_filter'] = filter_args
            cmd_line_args.add('test_filter')

        # Cmdline supports shuffle ordering only for now
        if 'shuffle' in cmd_line_args:
            shuffle_seed = args['shuffle_seed'] \
                if 'shuffle_seed' in cmd_line_args \
                else args['shuffle_seed'].value,
            args['test_sorter'] = ordering.ShuffleSorter(
                seed=shuffle_seed,
                shuffle_type=args['shuffle']
            )
        else:
            args['test_sorter'] = ordering.NoopSorter()

        # Set stdout style and logging level options according to
        # verbose/debug parameters. Debug output should be a superset of
        # verbose output, i.e. running with just "-d" should automatically
        # give you all "-v" output plus extra DEBUG logs.
        if 'verbose' in cmd_line_args and args['verbose'] or \
                'debug' in cmd_line_args and args['debug']:
            args['stdout_style'] = styles.Style(
                styles.StyleEnum.ASSERTION_DETAIL,
                styles.StyleEnum.ASSERTION_DETAIL)
            cmd_line_args.add('stdout_style')
            if 'debug' in cmd_line_args and args['debug']:
                args['logger_level'] = logger.DEBUG
                cmd_line_args.add('logger_level')
            else:
                args['logger_level'] = logger.INFO

        if 'list' in cmd_line_args and 'test_lister' not in cmd_line_args:
            args['test_lister'] = listing.NameLister()
            cmd_line_args.add('test_lister')

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
    LEVELS['NONE'] = None

    def __call__(self, parser, namespace, values, option_string=None):
        """Store the log level value corresponding to the level's name."""
        setattr(namespace, self.dest, self.LEVELS[values])
