import pytest

from testplan.common.utils.testing import check_report
from testplan.importers.gtest import GTestResultImporter
from tests.unit.testplan.importers.fixtures import gtest_failing, gtest_passing


@pytest.mark.parametrize(
    "params",
    (gtest_failing.fixture, gtest_passing.fixture),
)
def test_import(params):
    input_path = params.input_path
    importer = GTestResultImporter(
        input_path,
        name=params.expected_report.name,
        description=params.expected_report.description,
    )
    result = importer.import_result()
    check_report(
        expected=params.expected_report,
        actual=result.as_test_report(),
    )
