"""TODO."""
import argparse
import copy
import os
import random
import sys

import testplan.logger
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
            help='Shortcut for `--info name`'
        )

        parser.add_argument(
            '--info',
            dest='test_lister',
            metavar='TEST_INFO',
            **listing.ListingArg.get_parser_context(default=None)
        )

        general_group = parser.add_argument_group('General')
        general_group.add_argument(
            '--runpath', type=str, metavar='PATH',
            help='Path under which all temp files and logs will be created')

        filter_group = parser.add_argument_group('Filtering')

        filter_group.add_argument(
            '--patterns', action=filtering.PatternAction,
            default=[], nargs='+', metavar='TEST_FILTER', type=str,
            help=os.linesep.join([
                'Test filter, supports glob notation & multiple arguments.',
                '',
                '--pattern <Multitest Name>',
                '--pattern <Multitest Name 1> <Multitest Name 2>',
                '--pattern <Multitest Name 1> --pattern <Multitest Name 2>',
                '--pattern <Multitest Name>:<Suite Name>',
                '--pattern <Multitest Name>:<Suite Name>:<Testcase name>',
                '--pattern <Multitest Name>:*:<Testcase name>',
                '--pattern *:<Suite Name>:<Testcase name>',
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
            '--shuffle', nargs='+', type=str, default=[],
            choices=[enm.value for enm in ordering.SortType],
            help='Shuffle execution order')

        ordering_group.add_argument(
            '--shuffle-seed', metavar='SEED', type=float,
            default=float(random.randint(1, 9999)),
            help='Seed shuffle with a specific value, useful to '
                 'reproduce a particular order.')

        report_group = parser.add_argument_group('Reporting')

        report_group.add_argument(
            '--stdout-style',
            **styles.StyleArg.get_parser_context(
                default='summary'))

        report_group.add_argument(
            '--pdf', dest='pdf_path',
            default=None, metavar='PATH',
            help='Path for PDF report.'
        )

        report_group.add_argument(
            '--json', dest='json_path',
            default=None, metavar='PATH',
            help='Path for JSON report.'
        )

        report_group.add_argument(
            '--xml', dest='xml_dir',
            default=None, metavar='DIRECTORY',
            help='Directory path for XML reports.'
        )

        report_group.add_argument(
            '--report-dir',
            help='Target directory for tag filtered report output.',
            default=defaults.REPORT_DIR, metavar='PATH')

        report_group.add_argument(
            '--pdf-style',
            **styles.StyleArg.get_parser_context(
                default='extended-summary'))

        report_group.add_argument(
            '-v', '--verbose', action='store_true', dest='verbose',
            help='Enable verbose mode that will also set the stdout-style '
                 'option to "detailed".')
        report_group.add_argument(
            '-d', '--debug', action='store_true', dest='debug',
            help='Enable debug mode.')

        report_group.add_argument(
            '-b', '--browse', action='store_true', dest='browse',
            help='Automatically open report to browse.')

        report_group.add_argument(
            '--report-tags', nargs='+',
            action=ReportTagsAction,
            default=[],
            metavar='REPORT_FILTER',
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
            action=ReportTagsAction,
            default=[],
            metavar='REPORT_FILTER',
            help=os.linesep.join([
                'Report filter, generates a separate report (PDF by default)',
                'that match ALL of the given tags.',
                '',
                '--report-tags-all <tag_name_1> --report-tags-all <tag_name 2>',
                '--report-tags-all <tag_name_1> <tag_category_1>=<tag_name_2>',
            ])
        )

        report_group.add_argument(
            '-r', '--resource-monitor', action='store_true', dest='resource_monitor',
            help='Enable resource monitor that will record hosts resource statistics and event start & stop times')

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
            parsed_args=args,
            arg_names=('tags', 'tags_all', 'patterns'))

        if filter_args:
            args['test_filter'] = filter_args

        # Cmdline supports shuffle ordering only for now
        if 'shuffle' in args:
            args['test_sorter'] = ordering.ShuffleSorter(
                seed=args['shuffle_seed'],
                shuffle_type=args['shuffle']
            )

        if args['verbose'] is True:
            args['logger_level'] = testplan.logger.INFO
            testplan.logger.TESTPLAN_LOGGER.setLevel(testplan.logger.INFO)
            args['stdout_style'] = styles.Style(
                styles.StyleEnum.ASSERTION_DETAIL,
                styles.StyleEnum.ASSERTION_DETAIL)
        if args['debug'] is True:
            args['logger_level'] = testplan.logger.DEBUG
            testplan.logger.TESTPLAN_LOGGER.setLevel(testplan.logger.DEBUG)

        if args['list'] and 'info' not in args:
            args['test_lister'] = listing.NameLister()

        return args
