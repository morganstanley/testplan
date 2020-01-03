import pytest

from testplan.report.testing import styles


@pytest.mark.parametrize(
    'arg,display_result,display_test,display_testsuite,'
    'display_testcase,display_assertion,display_assertion_detail',
    (
        ('result', True, False, False, False, False, False),
        ('test', True, True, False, False, False, False),
        ('testsuite', True, True, True, False, False, False),
        ('testcase', True, True, True, True, False, False),
        ('assertion', True, True, True, True, True, False),
        ('assertion-detail', True, True, True, True, True, True),
    )
)
def test_output_style(
    arg, display_result, display_test, display_testsuite,
    display_testcase, display_assertion, display_assertion_detail
):
    style = styles.StyleFlag(arg)

    assert style.display_result == display_result
    assert style.display_test == display_test
    assert style.display_testsuite == display_testsuite
    assert style.display_testcase == display_testcase
    assert style.display_assertion == display_assertion
    assert style.display_assertion_detail == display_assertion_detail


def test_output_styles():
    """Str label initialization should create correct StyleFlag objects."""
    output_styles = styles.Style('testcase', 'assertion-detail')
    passing_style = styles.StyleFlag('testcase')
    failing_style = styles.StyleFlag('assertion-detail')

    assert output_styles.passing == passing_style
    assert output_styles.failing == failing_style
    assert output_styles.get_style(passing=True) == passing_style
    assert output_styles.get_style(passing=False) == failing_style
