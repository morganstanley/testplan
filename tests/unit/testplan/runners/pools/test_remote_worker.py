"""Remote worker bootstrap tests."""

import shlex
from unittest.mock import MagicMock, call

import pytest

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
    stdin.write.assert_called_once_with(b"/workspace\n/testplan with spaces")
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
