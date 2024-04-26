from testplan.common.entity import ResourceStatus
from testplan.common.report import RuntimeStatus, Status


def prev_assertions(report):
    assert report.entries[0].env_status == ResourceStatus.STARTED
    suite_report = report.entries[0].entries[0]
    assert suite_report.entries[0].name == "case_1"
    assert suite_report.entries[0].status == Status.FAILED
    assert suite_report.entries[0].runtime_status == RuntimeStatus.FINISHED
    assert suite_report.entries[1].name == "case_2"
    assert suite_report.entries[1].status == Status.PASSED
    assert suite_report.entries[1].runtime_status == RuntimeStatus.FINISHED
    assert suite_report.entries[2].name == "case_3"
    assert suite_report.entries[2].status == Status.PASSED
    assert suite_report.entries[2].runtime_status == RuntimeStatus.FINISHED


def curr_assertions(report):
    assert report.entries[0].env_status == ResourceStatus.STARTED
    suite_report = report.entries[0].entries[0]
    assert suite_report.entries[0].name == "case_1"
    assert suite_report.entries[0].status == Status.UNKNOWN
    assert suite_report.entries[0].runtime_status == RuntimeStatus.READY
    assert not len(suite_report.entries[0].entries)
    assert suite_report.entries[1].entries[0].name == "case_3 <arg=0>"
    assert suite_report.entries[1].entries[0].status == Status.UNKNOWN
    assert (
        suite_report.entries[1].entries[0].runtime_status
        == RuntimeStatus.READY
    )
    assert suite_report.entries[1].entries[1].name == "case_3 <arg=1>"
    assert suite_report.entries[1].entries[1].status == Status.UNKNOWN
    assert (
        suite_report.entries[1].entries[1].runtime_status
        == RuntimeStatus.READY
    )
