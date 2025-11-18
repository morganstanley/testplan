import pytest
import os
import psutil

from testplan.common.report import ReportCategories
from testplan.report.testing import TestGroupReport
from testplan.runnable.base import collate_for_merging, TestRunner


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


class TestPidFileCheck:
    """Tests for PID file checking functionality"""

    def test_check_pidfile_no_file(self, tmpdir):
        """Test when no PID file exists"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")
        plan._check_pidfile()

    def test_check_pidfile_empty_file(self, tmpdir):
        """Test when PID file is empty"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        with open(plan._pidfile_path, "w") as f:
            f.write("")

        plan._check_pidfile()

    def test_check_pidfile_invalid_content(self, tmpdir):
        """Test when PID file contains invalid content"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        with open(plan._pidfile_path, "w") as f:
            f.write("not_a_number")

        plan._check_pidfile()

    def test_check_pidfile_current_process(self, tmpdir):
        """Test when PID file contains current process PID"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        current_pid = os.getpid()
        with open(plan._pidfile_path, "w") as f:
            f.write(str(current_pid))

        plan._check_pidfile()

    def test_check_pidfile_stale_pid(self, tmpdir):
        """Test when PID file contains a non-existent PID"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        fake_pid = 999999
        while psutil.pid_exists(fake_pid):
            fake_pid += 1

        with open(plan._pidfile_path, "w") as f:
            f.write(str(fake_pid))

        plan._check_pidfile()

    def test_check_pidfile_another_process(self, tmpdir):
        """Test when PID file contains another running process PID"""
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        current_pid = os.getpid()
        other_pid = None
        for proc in psutil.process_iter(["pid"]):
            if proc.pid != current_pid and proc.pid != 1:
                other_pid = proc.pid
                break

        if other_pid is None:
            pytest.skip("Could not find another running process for testing")

        with open(plan._pidfile_path, "w") as f:
            f.write(str(other_pid))

        with pytest.raises(
            RuntimeError,
            match=f"Another testplan instance with PID {other_pid}",
        ):
            plan._check_pidfile()
