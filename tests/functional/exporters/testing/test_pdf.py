import os

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan.testing.multitest.entries import base
from testplan.testing.multitest.entries.schemas.base import registry

from testplan import Testplan, defaults
from testplan.common.utils.testing import (
    log_propagation_disabled, argv_overridden
)
from testplan.exporters.testing.pdf import PDFExporter, TagFilteredPDFExporter
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.report.testing import (
    TestReport, TestCaseReport, TestGroupReport, ReportCategories,
)
from testplan.report.testing import styles
from testplan.testing.multitest.entries import assertions


def test_create_pdf(tmpdir):
    """PDF exporter should generate a PDF file using the report data."""
    pdf_path = tmpdir.mkdir('reports').join('dummy_report.pdf').strpath

    assertion_entries = [
        assertions.Equal(1, 2),
        assertions.Greater(2, 1),
        assertions.IsFalse(True, 'this should fail'),
        assertions.IsTrue(True, 'this should pass'),
        assertions.Fail('Explicit failure'),
        base.Group(
            description='group description',
            entries=[
                assertions.NotEqual(2, 1),
                assertions.Contain(1, [1, 2, 3]),
            ]
        )
    ]

    report = TestReport(
        name='my testplan',
        entries=[
            TestGroupReport(
                name='My Multitest',
                category==ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name='MySuite',
                        category=ReportCategories.SUITE,
                        entries=[
                            TestCaseReport(
                                name='my_test_method',
                                entries=[
                                    registry.serialize(obj)
                                    for obj in assertion_entries
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    exporter = PDFExporter(
        pdf_path=pdf_path,
        pdf_style=styles.Style(
            passing='assertion-detail',
            failing='assertion-detail'
        )
    )

    with log_propagation_disabled(TESTPLAN_LOGGER):
        exporter.export(report)

    assert os.path.exists(pdf_path)
    assert os.stat(pdf_path).st_size > 0


def test_tag_filtered_pdf(tmpdir):
    """
        Tag filtered PDF exporter should generate
        multiple PDF files for matching report sub-trees
        and skip empty reports.
    """
    pdf_dir = tmpdir.mkdir('reports').strpath

    report = TestReport(
        name='my testplan',
        entries=[
            TestGroupReport(
                name='Multitest 1',
                category=ReportCategories.MULTITEST,
                tags={
                    'simple': {'foo', 'bar'},
                    'color': {'red'}
                },
            ),
            TestGroupReport(
                name='Multitest 2',
                category=ReportCategories.MULTITEST,
                tags={
                    'simple': {'foo'},
                    'color': {'blue'}
                },
            ),
            TestGroupReport(
                name='Multitest 3',
                category=ReportCategories.MULTITEST,
                tags={
                    'simple': {'bar'},
                    'color': {'green'}
                },
            ),
        ]
    )

    exporter = TagFilteredPDFExporter(
        report_dir=pdf_dir,
        pdf_style=defaults.PDF_STYLE,
        report_tags=[
            'foo',
            'baz',  # this should be skipped
            {'simple': 'bar', 'color': ['blue', 'green']}
        ],
        report_tags_all=[
            ('foo', 'bar'),
            # this should be skipped
            {
                'simple': ('foo', 'bar'),
                'color': 'green',
            }
        ],
    )

    with log_propagation_disabled(TESTPLAN_LOGGER):
        exporter.export(report)

    should_exist = [
        'report-tags-all-bar__foo.pdf',
        'report-tags-any-bar__color-blue-green.pdf',
        'report-tags-any-foo.pdf',
    ]

    should_not_exist = [
        'report-tags-all-bar__foo__color-green.pdf',
        'report-tags-any-baz.pdf'
    ]

    for path in should_exist:
        path = os.path.join(pdf_dir, path)
        assert os.path.exists(path), 'Could not generate PDF: {}'.format(path)
        assert os.stat(path).st_size > 0

    for path in should_not_exist:
        path = os.path.join(pdf_dir, path)
        assert not os.path.exists(path), (
            'Should not have been generated PDF: {}'.format(path))


def test_implicit_exporter_initialization(tmpdir):
    """
        An implicit PDFExporter should be generated if `pdf_path` is available
        via cmdline args but no exporters were declared.

        Multiple implicit TagFilteredPDFExporters should be initialized
        if `report_tags` or `report_tags_all` arguments are passed
        via cmdline, but no exporters were declared.
    """
    pdf_dir = tmpdir.mkdir('reports')
    pdf_path = pdf_dir.join('my_report.pdf').strpath

    @testsuite
    class MySuite(object):

        @testcase
        def test_comparison(self, env, result):
            result.equal(1, 1, 'equality description')

        @testcase(tags='foo')
        def test_membership(self, env, result):
            result.contain(1, [1, 2, 3])

    with log_propagation_disabled(TESTPLAN_LOGGER):
        with argv_overridden(
            '--pdf', pdf_path,
            '--report-tags', 'foo',
            '--report-dir', pdf_dir.strpath
        ):
            multitest = MultiTest(
                name='MyMultitest', suites=[MySuite()])

            plan = Testplan(name='plan')
            plan.add(multitest)
            plan.run()

    tag_pdf_path = pdf_dir.join('report-tags-any-foo.pdf').strpath
    assert os.path.exists(pdf_path)
    assert os.path.exists(tag_pdf_path)
    assert os.stat(pdf_path).st_size > 0
    assert os.stat(tag_pdf_path).st_size > 0
