import getpass
import os
import shutil
import tempfile

import pytest

from testplan import TestplanMock
from testplan.common.utils.path import rebase_path
from testplan.common.utils.remote import filepath_exist_cmd

REMOTE_HOST = os.environ.get("TESTPLAN_REMOTE_HOST")
pytestmark = pytest.mark.skipif(
    not REMOTE_HOST,
    reason="Remote host not specified, skip remote resource test",
)

from testplan.common.remote.remote_resource import RemoteResource


@pytest.fixture(scope="function")
def workspace():
    """
    Sets up the workspace to use for testing the remote resource. We will copy the
    tests subdir to workspace, and remote resource logic will copy the workspace
    to remote host.

    :return: paths to the workspace
    """
    # Set up the workspace in a temporary directory.
    workspace = tempfile.mkdtemp()

    # Copy the tests dir. "tests" is a generic name so we don't want to
    # rely "import tests" here - instead navigate up to find the tests dir.
    script_dir = os.path.dirname(__file__)

    # get GIT_ROOT/tests
    orig_tests_dir = script_dir
    while os.path.basename(orig_tests_dir) != "tests":
        orig_tests_dir = os.path.abspath(
            os.path.join(orig_tests_dir, os.pardir)
        )

    shutil.copytree(orig_tests_dir, os.path.join(workspace, "tests"))

    working_dir = rebase_path(
        script_dir, orig_tests_dir, os.path.join(workspace, "tests")
    )

    orig_dir = os.getcwd()
    os.chdir(working_dir)

    yield workspace

    os.chdir(orig_dir)
    shutil.rmtree(workspace)


@pytest.fixture(scope="module")
def push_dir():
    push_dir = tempfile.mkdtemp()
    for filename in ("file1", "file2", "file3"):
        path = os.path.join(push_dir, filename)
        with open(path, "w") as fobj:
            fobj.write(path)

    import subprocess

    subprocess.check_output(["ln", "-sfn", "file1", "file1_ln"], cwd=push_dir)

    yield push_dir

    shutil.rmtree(push_dir)


@pytest.fixture(scope="function")
def remote_resource(runpath_module, workspace, push_dir):
    mockplan = TestplanMock("plan", runpath=runpath_module)

    push = [
        push_dir,  # push dir to same path on remote
        ("/".join([push_dir, "file1"]), "file1"),  # dst is rel to working_dir
        (
            "/".join([push_dir, "file2"]),
            "/".join([workspace, "file2"]),
        ),  # dst is abs path
    ]

    remote_resource = RemoteResource(
        REMOTE_HOST,
        workspace=workspace,
        workspace_exclude=[
            "conftest.py",
            "helpers",
            "*unctiona*",
            "__pycache__",
            "*.pyc",
        ],
        push=push,
        push_exclude=["*file3"],
        delete_pushed=True,
        fetch_runpath_exclude=[],
        pull=[push_dir],  # pull back push_dir
        pull_exclude=["file2"],
        env={"LOCAL_USER": getpass.getuser()},
        setup_script=["remote_setup.py"],
        check_remote_python_ver=False,
        clean_remote=True,
    )
    remote_resource.parent = mockplan.runnable
    remote_resource.cfg.parent = mockplan.runnable.cfg

    yield remote_resource


def test_prepare_remote(remote_resource, workspace, push_dir):
    remote_resource.make_runpath_dirs()
    remote_resource._prepare_remote()

    assert (
        remote_resource._remote_plan_runpath == remote_resource.parent.runpath
    )
    assert remote_resource._remote_resource_runpath == remote_resource.runpath
    assert remote_resource._remote_runid_file == "/".join(
        [
            remote_resource._remote_plan_runpath,
            remote_resource.parent.runid_filename,
        ]
    )
    assert remote_resource._workspace_paths.remote == "/".join(
        [remote_resource._remote_plan_runpath, "fetched_workspace"]
    )

    assert remote_resource._working_dirs.remote == rebase_path(
        os.getcwd(),
        workspace,
        remote_resource._workspace_paths.remote,
    )

    for remote_path in [
        remote_resource._remote_runid_file,
        "/".join([remote_resource._workspace_paths.remote, "tests", "unit"]),
        "/".join([push_dir, "file1"]),
        "/".join([push_dir, "file1_ln"]),
        "/".join([remote_resource._working_dirs.remote, "file1"]),
        "/".join([workspace, "file2"]),
        # so that we know the default SourceTransferBuilder has done its job
        "/".join(
            [
                remote_resource._remote_plan_runpath,
                remote_resource._remote_runtime_builder.cfg._runpath_testplan_dir,
                "testplan",
                "version.py",
            ]
        ),
    ]:
        assert (
            0
            == remote_resource._ssh_client.exec_command(
                cmd=filepath_exist_cmd(remote_path),
                check=False,
            )[0]
        )

    for remote_path in [
        "/".join(
            [remote_resource._workspace_paths.remote, "tests", "functional"]
        ),
        "/".join([push_dir, "file3"]),
    ]:
        assert (
            0
            != remote_resource._ssh_client.exec_command(
                cmd=filepath_exist_cmd(remote_path),
                check=False,
            )[0]
        )

    # for now, these setting are used by child.py rather than remote_resource
    assert remote_resource.setup_metadata.env == {
        "LOCAL_USER": getpass.getuser()
    }
    assert remote_resource.setup_metadata.setup_script == ["remote_setup.py"]
    assert remote_resource.setup_metadata.push_dirs == [push_dir]
    assert remote_resource.setup_metadata.push_files == [
        "/".join([remote_resource._working_dirs.remote, "file1"]),
        "/".join([workspace, "file2"]),
    ]

    remote_resource._clean_remote()


def test_fetch_results(remote_resource, push_dir):
    remote_resource.make_runpath_dirs()
    remote_resource._prepare_remote()

    log_file = "/".join(
        [remote_resource._remote_resource_runpath, "remote.log"]
    )

    remote_resource._ssh_client.exec_command(
        cmd=f"/bin/touch {log_file}",
        label="create log file",
    )

    remote_resource._fetch_results()

    log_file_local = rebase_path(
        log_file,
        remote_resource._remote_plan_runpath,
        remote_resource.parent.runpath,
    )
    assert os.path.exists(log_file_local)
    assert os.path.exists(
        os.path.join(
            remote_resource.runpath,
            "pulled_files",
            os.path.basename(push_dir),
            "file1",
        )
    )
    assert not os.path.exists(
        os.path.join(
            remote_resource.runpath,
            "pulled_files",
            os.path.basename(push_dir),
            "file2",
        )
    )

    remote_resource._clean_remote()
    # TODO: test delete_pushed


def test_runpath_in_ws(workspace):
    mockplan = TestplanMock(
        "plan", runpath=os.path.join(workspace, "runpath_in_ws")
    )

    remote_resource = RemoteResource(
        REMOTE_HOST,
        workspace=workspace,
        workspace_exclude=[
            "conftest.py",
            "helpers",
            "*unctiona*",
            "__pycache__",
            "*.pyc",
        ],
        check_remote_python_ver=False,
        clean_remote=True,
    )
    remote_resource.parent = mockplan.runnable
    remote_resource.cfg.parent = mockplan.runnable.cfg

    try:
        remote_resource.make_runpath_dirs()
        remote_resource._prepare_remote()

        assert (
            0
            != remote_resource._ssh_client.exec_command(
                cmd=filepath_exist_cmd(
                    "/".join(
                        [
                            remote_resource._workspace_paths.remote,
                            "tests",
                            "functional",
                        ]
                    )
                ),
                check=False,
            )[0]
        )
    finally:
        remote_resource._clean_remote()

    assert (
        0
        != remote_resource._ssh_client.exec_command(
            cmd=filepath_exist_cmd(
                "/".join(
                    [
                        remote_resource._workspace_paths.remote,
                        "tests",
                    ]
                )
            ),
            check=False,
        )[0]
    )
