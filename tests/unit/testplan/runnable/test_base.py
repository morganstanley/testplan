import pytest
import os
import psutil

from testplan.common.report import ReportCategories
from testplan.common.utils.exceptions import RunpathInUseError
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
            RunpathInUseError,
            match=f"Another testplan instance with PID {other_pid}",
        ):
            plan._check_pidfile()

    def test_check_pidfile_stale_remote_process(self, tmpdir):
        """
        Test PID file with stale remote process {host}:{port};{pid} format.
        
        Verifies that when a PID file contains remote process information but
        the SSH connection (identified by host:port) is no longer ESTABLISHED,
        the check passes and allows the new testplan to proceed.
        """
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        existing_connections = set()
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                existing_connections.add((conn.raddr.ip, conn.raddr.port))

        fake_host = "192.0.2.1"
        fake_port = 65432

        while (fake_host, fake_port) in existing_connections:
            fake_port += 1

        fake_pid = 999999
        while psutil.pid_exists(fake_pid):
            fake_pid += 1

        with open(plan._pidfile_path, "w") as f:
            f.write(f"{fake_host}:{fake_port};{fake_pid}")

        plan._check_pidfile()

    def test_check_pidfile_active_remote_process(self, tmpdir):
        """
        Test PID file with active remote process {host}:{port};{pid} format.
        
        Verifies that when a PID file contains remote process information and
        an ESTABLISHED TCP connection to the specified host:port exists,
        a RunpathInUseError is raised to prevent concurrent testplan execution
        using the same runpath.
        """
        plan = TestRunner(name="test", parse_cmdline=False)
        plan._runpath = str(tmpdir)
        plan._pidfile_path = os.path.join(plan._runpath, "testplan.pid")

        active_conn = None
        for conn in psutil.net_connections(kind="tcp"):
            if (
                conn.status == psutil.CONN_ESTABLISHED
                and conn.raddr
                and conn.raddr.ip
                and conn.raddr.port
            ):
                active_conn = conn
                break

        if active_conn is None:
            pytest.skip("No active TCP connection found for testing")

        fake_pid = 999999
        while psutil.pid_exists(fake_pid):
            fake_pid += 1

        with open(plan._pidfile_path, "w") as f:
            f.write(
                f"{active_conn.raddr.ip}:{active_conn.raddr.port};{fake_pid}"
            )

        # Should raise because the connection exists
        with pytest.raises(
            RunpathInUseError,
            match=f"Another testplan instance on {active_conn.raddr.ip}",
        ):
            plan._check_pidfile()
