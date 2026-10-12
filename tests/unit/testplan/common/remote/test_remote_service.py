import os
from unittest import mock

import pytest

from testplan.common.remote.remote_service import RemoteService


@pytest.fixture
def service():
    svc = RemoteService.__new__(RemoteService)
    svc._tls_local_dir = None
    svc._tls_remote_dir = None
    svc._remote_resource_runpath = "/remote/run"
    svc._ssh_client = mock.MagicMock()
    svc._ssh_client.exec_command.return_value = (0, "", "")
    svc.proc = None
    svc.rpyc_connection = None
    return svc


def _remote_dir_deleted(svc, remote_dir):
    calls = svc._ssh_client.exec_command.call_args_list
    return any(
        c.kwargs.get("label") == "delete remote tls dir"
        and remote_dir in c.args[0]
        for c in calls
    )


def test_certs_deleted_after_connect(service):
    service._setup_tls()
    local_dir, remote_dir = service._tls_local_dir, service._tls_remote_dir
    assert os.path.isdir(local_dir)

    with (
        mock.patch.object(service, "_connect_tls"),
        mock.patch.object(service, "_remote_sys_path", return_value=[]),
        mock.patch.object(service, "_working_dirs", create=True),
    ):
        service._config_server()

    assert not os.path.exists(local_dir)
    assert _remote_dir_deleted(service, remote_dir)


def test_certs_deleted_if_fetch_fails(service):
    service._setup_tls()
    local_dir, remote_dir = service._tls_local_dir, service._tls_remote_dir

    with mock.patch.object(
        service, "_fetch_results", side_effect=OSError("fetch failed")
    ):
        with pytest.raises(OSError):
            service.pre_stop()

    assert not os.path.exists(local_dir)
    assert _remote_dir_deleted(service, remote_dir)
