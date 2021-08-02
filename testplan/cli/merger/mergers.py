from typing import Iterable

from testplan.report import TestReport


class SimpleCombiner:
    """
    Simple Combiner that just put each toplevel tests from
    testplans next to each other into a testplan
    """

    RESULT_DESCRIPTION_HEADER = "Merged report"

    @staticmethod
    def __heading(text, underline_char="="):
        return [text, underline_char * len(text), ""]

    def merge(self, reports: Iterable[TestReport]):

        result = TestReport(name="Combined Report")

        description = self.__heading(self.RESULT_DESCRIPTION_HEADER)

        for report in reports:
            result.attachments.update(report.attachments)
            result.extend(report.entries)
            result.logs.extend(report.logs)

            result.information.extend(report.information)
            description.extend(self.__heading(report.name))
            if report.description:
                description.append(f"{report.description}\n")

            # TODO: what to do with meta, tags_index
        result.description = "\n".join(description)

        return result
