import pytest

from testplan.common.report import ReportCategories
from testplan.report.testing import TestGroupReport
from testplan.runnable.base import collate_for_merging


@pytest.mark.parametrize(
    "entries",
    (
        [],
        [TestGroupReport("mt")],
        [
            TestGroupReport("mt"),
            TestGroupReport("st", category=ReportCategories.SYNTHESIZED),
        ],
    ),
)
def test_collate_for_merging(entries):
    res = collate_for_merging(entries)
    assert [e for t in res for e in t] == entries
    assert all(
        [t[0].category != ReportCategories.SYNTHESIZED for t in res if t]
    )
