import os

import pytest

from testplan.common.utils.testing import check_report, check_iterable
from testplan.importers.cppunit import CPPUnitResultImporter
from tests.unit.testplan.importers.fixtures import (
    cppunit_failing,
    cppunit_passing,
)


@pytest.mark.parametrize(
    "params",
    (cppunit_failing.fixture, cppunit_passing.fixture),
)
def test_import(params):
    input_path = params.input_pah
    importer = CPPUnitResultImporter(
        input_path,
        name=params.expected_report.name,
        description=params.expected_report.description,
    )
    result = importer.import_result()
    check_report(
        expected=params.expected_report,
        actual=result.as_test_report(),
    )
