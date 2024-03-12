from testplan.report.testing import Status, RuntimeStatus


def prev_assertions(report):
    case_report = report.entries[0].entries[0].entries[0]
    assert case_report.name == "case_1"
    assert case_report.runtime_status == RuntimeStatus.FINISHED
    assert case_report.status == Status.PASSED


def curr_assertions(report):
    suite_report = report.entries[0].entries[0]
    assert suite_report.entries[0].status == Status.PASSED
    assert len(suite_report.entries[0].entries)
    assert suite_report.entries[1].name == "case_2"
    assert suite_report.entries[1].status == Status.UNKNOWN
    assert suite_report.entries[1].runtime_status == RuntimeStatus.READY
    assert not len(suite_report.entries[1].entries)
