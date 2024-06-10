from typing import List

from testplan.common.utils.strings import uuid4
from testplan.importers import ImportedResult
from testplan.report import TestGroupReport, TestReport, ReportCategories


class SuitesResult(ImportedResult):

    REPORT_CATEGORY = ReportCategories.UNITTEST

    def __init__(
        self,
        name: str,
        results: List[TestGroupReport],
        description: str = None,
    ):
        """

        :param name: name will be used as the name of the plan and the single test
                     which will hold the suites from this result
        :param results:
        """

        self.name = name
        self._results = results
        self.description = description

    def as_test_report(self) -> TestReport:
        """

        :return: a plan report contains a single test having all the returned suite results
        """
        report = TestReport(
            name=self.name, description=self.description, uid=uuid4()
        )
        test_report = TestGroupReport(
            name=self.name,
            category=self.REPORT_CATEGORY,
            description=self.description,
            uid=uuid4(),
        )

        for suite_report in self.results():
            test_report.append(suite_report)

        report.append(test_report)
        return report

    def category(self) -> str:
        return ReportCategories.TESTSUITE

    def results(self) -> (List[TestGroupReport]):
        return self._results
