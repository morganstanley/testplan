"""Remote worker bootstrap tests."""

import ntpath
import os
import posixpath
import shlex
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from testplan.runners.pools import remote
from testplan.runners.pools.remote import RemoteWorker


@pytest.mark.parametrize("failure", [None, "write", "exit"])
def test_syspath_transfer_reuses_ssh_connection(tmp_path, failure):
    worker = object.__new__(RemoteWorker)
    worker.parent = MagicMock(runpath=str(tmp_path))
    worker._remote_plan_runpath = "/remote/runpath with 'quotes'"
    worker._remote_sys_path = MagicMock(
        return_value=["/workspace", "/testplan with spaces"]
    )
    worker._ssh_client = MagicMock()
    worker._transfer_data = MagicMock()
    worker._logger = MagicMock()
    channel = MagicMock()
    stdin, stdout, stderr = channel.stdin, channel.stdout, channel.stderr
    stdout.channel.recv_exit_status.return_value = (
        1 if failure == "exit" else 0
    )
    stderr.read.return_value = (
        b"Permission denied" if failure == "exit" else b""
    )
    worker._ssh_client.ssh_client.exec_command.return_value = (
        stdin,
        stdout,
        stderr,
    )

    if failure == "write":
        stdin.write.side_effect = OSError("connection lost")
        with pytest.raises(OSError, match="connection lost"):
            worker._write_syspath()
    elif failure == "exit":
        with pytest.raises(
            RuntimeError, match="exit code 1: Permission denied"
        ):
            worker._write_syspath()
    else:
        worker._write_syspath()

    worker._ssh_client.ssh_client.exec_command.assert_called_once_with(
        command=f"/bin/cat > {shlex.quote(worker._remote_syspath_file)}",
        timeout=30,
    )
    worker._transfer_data.assert_not_called()
    stdin.write.assert_called_once_with(
        f"/workspace{os.linesep}/testplan with spaces".encode()
    )
    if failure != "write":
        channel.assert_has_calls(
            [
                call.stdin.flush(),
                call.stdin.channel.shutdown_write(),
                call.stdout.channel.recv_exit_status(),
                call.stderr.read(),
            ]
        )
    stdin.close.assert_called_once_with()
    stdout.close.assert_called_once_with()
    stderr.close.assert_called_once_with()


@pytest.mark.parametrize(
    "controller_path", [posixpath, ntpath], ids=["posix", "windows"]
)
def test_syspath_transfer_matches_child_argument(
    tmp_path, monkeypatch, controller_path
):
    worker = object.__new__(RemoteWorker)
    worker.parent = MagicMock(
        runpath=str(tmp_path), resource_monitor_address=None
    )
    worker._remote_plan_runpath = "/remote/run"
    worker._remote_sys_path = MagicMock(return_value=["/workspace"])
    worker._ssh_client = MagicMock()
    worker._logger = MagicMock()
    stdin, stdout, stderr = MagicMock(), MagicMock(), MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stderr.read.return_value = b""
    worker._ssh_client.ssh_client.exec_command.return_value = (
        stdin,
        stdout,
        stderr,
    )

    with monkeypatch.context() as patch:
        path = SimpleNamespace(
            join=controller_path.join, basename=os.path.basename
        )
        patch.setattr(remote, "os", SimpleNamespace(path=path))
        worker._write_syspath()

    transfer_cmd = worker._ssh_client.ssh_client.exec_command.call_args.kwargs[
        "command"
    ]
    destination = shlex.split(transfer_cmd)[-1]
    basename = os.path.basename(worker._syspath_file)
    assert destination == f"/remote/run/sys_path_{basename}"

    worker._cfg = SimpleNamespace(
        index="worker-0",
        pool_type="thread",
        workers=1,
        ssh_cmd=lambda cfg, command: command,
    )
    worker.ssh_cfg = {}
    worker._remote_pybin = "/usr/bin/python3"
    worker._child_paths = SimpleNamespace(remote="/workspace/child.py")
    worker._working_dirs = SimpleNamespace(remote="/workspace")
    worker._remote_resource_runpath = "/remote/run/worker-0"
    worker.transport = MagicMock(address="controller:1234")

    child_argv = shlex.split(worker._proc_cmd())
    assert child_argv[child_argv.index("--sys-path-file") + 1] == destination
