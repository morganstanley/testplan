import subprocess

from testplan.common.utils.remote import copy_cmd


def mock_ssh(host, command):
    """Avoid network connection."""
    return ["/bin/sh", "-c", command]


def strip_host(source, target, **kwargs):
    """Avoid network connection."""
    if ":" in source:
        source = source.split(":")[1]
    if ":" in target:
        target = target.split(":")[1]
    return copy_cmd(source, target)


def copytree(src, dst):
    """
    We can't use shutil.copytree() with python 3.4.4 due to
    https://bugs.python.org/issue21697 so use rsync instead.
    """
    subprocess.check_call(
        [
            "rsync",
            "-rL",
            "--exclude=.git",
            "--exclude=*.pyc",
            "--exclude=*__pycache__*",
            src,
            dst,
        ]
    )