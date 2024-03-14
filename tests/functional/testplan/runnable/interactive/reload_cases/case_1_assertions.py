from testplan.common.entity import ResourceStatus
from testplan.report.testing import RuntimeStatus, Status


def prev_assertions(report):
    assert report.entries[0].env_status == ResourceStatus.STARTED
    case_report = report.entries[0].entries[0].entries[0]
    assert case_report.name == "case_1"
    assert case_report.status == Status.FAILED
    assert case_report.runtime_status == RuntimeStatus.FINISHED
    assert case_report.entries[0].name == "case_1 <arg=0>"
    assert case_report.entries[0].status == Status.PASSED
    assert case_report.entries[0].runtime_status == RuntimeStatus.FINISHED
    assert case_report.entries[1].name == "case_1 <arg=1>"
    assert case_report.entries[1].status == Status.FAILED
    assert case_report.entries[1].runtime_status == RuntimeStatus.FINISHED


def curr_assertions(report):
    assert report.entries[0].env_status == ResourceStatus.STARTED
    case_report = report.entries[0].entries[0].entries[0]
    assert case_report.name == "case_1"
    assert case_report.status == Status.FAILED
    assert case_report.runtime_status == RuntimeStatus.READY
    assert case_report.entries[0].name == "case_1 <arg=0>"
    assert case_report.entries[0].status == Status.PASSED
    assert case_report.entries[0].runtime_status == RuntimeStatus.FINISHED
    assert len(case_report.entries[0].entries)
    assert case_report.entries[1].name == "case_1 <arg=1>"
    assert case_report.entries[1].status == Status.FAILED
    assert case_report.entries[1].runtime_status == RuntimeStatus.FINISHED
    assert len(case_report.entries[1].entries)
    assert case_report.entries[2].name == "case_1 <arg=2>"
    assert case_report.entries[2].status == Status.UNKNOWN
    assert case_report.entries[2].runtime_status == RuntimeStatus.READY
    assert not len(case_report.entries[2].entries)
