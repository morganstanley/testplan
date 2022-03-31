import pytest

from testplan.common.utils.testing import check_report
from testplan.importers.junit import JUnitResultImporter
from .fixtures import (
    junit_binary,
    junit_testsuite,
    junit_testsuites,
)


@pytest.mark.parametrize(
    "params",
    (
        junit_binary.fixture,
        junit_testsuite.fixture,
        junit_testsuites.fixture,
    ),
)
def test_import(params):
    input_path = params.input_path
    importer = JUnitResultImporter(
        input_path,
        name=params.expected_report.name,
        description=params.expected_report.description,
    )
    result = importer.import_result()
    check_report(
        expected=params.expected_report,
        actual=result.as_test_report(),
    )
