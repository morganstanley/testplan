"""
Test Multitest - Test Suite - Result - Test Report - Exporter
integration on local runner
"""
import os

import pytest

from testplan import Testplan, Task
from testplan.runners.pools import ProcessPool

from testplan.common.utils.testing import check_report, log_propagation_disabled

from testplan.exporters.testing import PDFExporter
from testplan.common.utils.logger import TESTPLAN_LOGGER


from ..fixtures import assertions_failing, assertions_passing
try:
    from ..fixtures import matplotlib
except ImportError as e:
    matplot_make_multitest = None
    matplot_expected_report = None
else:
    matplot_make_multitest = matplotlib.suites.make_multitest
    matplot_expected_report = matplotlib.report.expected_report


def importorxfail(dependency):
    """
    Try to import dependency, mark test as xfail if not.

    :param dependency: Dependency to try importing.
    :type dependency: ``str``
    """
    try:
        __import__(dependency)
    except ImportError as e:
        pytest.xfail(str(e))

@pytest.fixture(scope='session')
def report_dir(tmpdir_factory):
    """
    `tmpdir` fixture is somehow failing for this module, so this fixture
    explicitly makes sure that given basetemp exists.
    """
    basetemp = tmpdir_factory.getbasetemp().strpath
    if not os.path.exists(basetemp):
        os.makedirs(basetemp)
    return tmpdir_factory.mktemp('report')


@pytest.mark.parametrize(
    ('multitest_maker,expected_report,pdf_title,'
    'expected_plan_result,dependant_module'),
    (
        (
            assertions_passing.suites.make_multitest,
            assertions_passing.report.expected_report,
            'True',
            True,
            None,
        ),
        (
            assertions_failing.suites.make_multitest,
            assertions_failing.report.expected_report,
            'False',
            False,
            None,
        ),
        (
            matplot_make_multitest,
            matplot_expected_report,
            'Matplotlib',
            True,
            'matplotlib.pyplot'
        ),
    )
)
def test_local_pool_integration(
    report_dir, multitest_maker,
    expected_report, pdf_title,
    expected_plan_result, dependant_module
):
    if dependant_module:
        importorxfail(dependant_module)

    pdf_path = report_dir.join('test_report_local_{}.pdf'.format(
        pdf_title)).strpath
    plan = Testplan(
        name='plan',
        parse_cmdline=False,
        exporters=[
            PDFExporter.with_config(pdf_path=pdf_path)
        ]
    )

    plan.add(multitest_maker())

    assert not os.path.exists(pdf_path)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    for log in plan.report.flattened_logs:
        if all(word in log['message'] for word in ['tkinter', 'TclError']):
            pytest.xfail(reason='Tkinter not installed properly')

    check_report(expected=expected_report, actual=plan.report)

    assert plan.result.success is expected_plan_result
    assert os.path.exists(pdf_path)
    assert os.stat(pdf_path).st_size > 0


@pytest.mark.parametrize(
    ('fixture_dirname,expected_report,pdf_title,'
     'expected_plan_result,dependant_module'),
    (
        (
            'assertions_passing',
            assertions_passing.report.expected_report,
            'True',
            True,
            None,
        ),
        (
            'assertions_failing',
            assertions_failing.report.expected_report,
            'False',
            False,
            None,
        ),
        (
            'matplotlib',
            matplot_expected_report,
            'Matplotlib',
            True,
            'matplotlib.pyplot'
        ),
    )
)
def test_process_pool_integration(
    report_dir, fixture_dirname,
    expected_report, pdf_title,
    expected_plan_result, dependant_module
):
    if dependant_module:
        importorxfail(dependant_module)

    pool = ProcessPool(name='MyPool', size=1)
    pdf_path = report_dir.join('test_report_process_{}.pdf'.format(
        pdf_title)).strpath

    plan = Testplan(
        name='plan',
        parse_cmdline=False,
        exporters=[
            PDFExporter(pdf_path=pdf_path)
        ]
    )
    plan.add_resource(pool)

    runners_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fixture_path = os.path.join(runners_path, 'fixtures', fixture_dirname)

    task = Task(
        target='make_multitest',
        module='suites',
        path=fixture_path,
    )
    plan.schedule(task, resource='MyPool')

    assert not os.path.exists(pdf_path)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    for log in plan.report.flattened_logs:
        if all(word in log['message'] for word in ['tkinter', 'TclError']):
            pytest.xfail(reason='Tkinter not installed properly')

    check_report(expected=expected_report, actual=plan.report)

    assert plan.result.success is expected_plan_result
    assert os.path.exists(pdf_path)
    assert os.stat(pdf_path).st_size > 0
