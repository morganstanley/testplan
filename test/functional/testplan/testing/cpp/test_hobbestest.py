import os
import platform

import pytest

from testplan import Testplan
from testplan.common.utils.testing import log_propagation_disabled, check_report
from testplan.logger import TESTPLAN_LOGGER
from testplan.testing.cpp import HobbesTest

from test.functional.testplan.testing.fixtures.cpp import hobbestest

fixture_root = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'fixtures',
    'cpp',
    'hobbestest'
)

BINARY_NOT_FOUND_MESSAGE = '''
Hobbes test binary not found at: "{binary_path}", this test will be skipped.
You can either use the mock test binary or replace it with a link to the actual Hobbes test binary to run this test.
'''


@pytest.mark.skipif(
    platform.system() == 'Windows',
    reason='HobbesTest is skipped on Windows.'
)
@pytest.mark.parametrize(
    'binary_dir, expected_report',
    (
        (
            os.path.join(fixture_root, 'failing'),
            hobbestest.failing.report.expected_report,
        ),
        (
            os.path.join(fixture_root, 'passing'),
            hobbestest.passing.report.expected_report,
        ),
    )
)
def test_hobbestest(binary_dir, expected_report):

    binary_path = os.path.join(binary_dir, 'hobbes-test')

    if not os.path.exists(binary_path):
        msg = BINARY_NOT_FOUND_MESSAGE.format(
            binary_dir=binary_dir,
            binary_path=binary_path
        )
        pytest.skip(msg)

    plan = Testplan(
        name='plan',
        parse_cmdline=False,
    )

    plan.add(HobbesTest(name='MyHobbesTest', driver=binary_path, tests=['Hog', 'Net', 'Recursives']))

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    check_report(expected=expected_report, actual=plan.report)
