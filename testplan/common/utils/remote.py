"""Remote execution utilities."""

import getpass
import os
import platform
import shlex
import socket
import subprocess
import sys
import time

import paramiko

from testplan.common.utils.logger import TESTPLAN_LOGGER

IS_WIN = platform.system() == "Windows"
USER = getpass.getuser()
DEFAULT_SSH_OPT = "-p {port} {user}@{host}"


def worker_is_remote(remote_host):
    """
    Check remote_host is not the same as current.
    """
    try:
        socket.inet_aton(remote_host)
    except socket.error:
        remote_ip = socket.gethostbyname(remote_host)
    else:
        remote_ip = remote_host

    local_ip = socket.gethostbyname(socket.gethostname())

    return local_ip != remote_ip


def ssh_bin():
    try:
        binary = os.environ["SSH_BINARY"]
    except KeyError:
        if IS_WIN:
            raise Exception("SSH binary not provided.")
        else:
            binary = (
                subprocess.check_output("which ssh", shell=True)
                .decode(sys.stdout.encoding)
                .strip()
            )
    return binary


def ssh_cmd(ssh_cfg, command):
    """
    Prefix command with ssh binary and option.

    :param ssh_cfg: dict with "host" and "port" (optional) keys
    :param command: command to execute on remote host
    :return: full cmd list
    """
    full_cmd = [ssh_bin()]

    ssh_opt = os.environ.get("SSH_OPT") or DEFAULT_SSH_OPT

    full_cmd.extend(
        ssh_opt.format(
            port=ssh_cfg.get("port", 22),
            user=USER,
            host=ssh_cfg["host"],
        ).split(" ")
    )
    full_cmd.append(command)
    return full_cmd


def copy_cmd(
    source: str, target: str, exclude=None, port=None, deref_links=False
):
    """Returns remote copy command."""
    # TODO: global rsync/scp selection
    try:
        binary = os.environ["RSYNC_BINARY"]
    except KeyError:
        if IS_WIN:
            binary = None
        else:
            binary = (
                subprocess.check_output("which rsync", shell=True)
                .decode(sys.stdout.encoding)
                .strip()
            )

    if binary:
        full_cmd = [binary, "-r", "-L" if deref_links else "-l"]

        if exclude is not None:
            for item in exclude:
                full_cmd.extend(["--exclude", item])

        if port is not None:
            # Add '-e "ssh -p "' option to rsync command
            ssh = "{} -p {}".format(ssh_bin(), port)
            full_cmd.extend(["-e", ssh])

        full_cmd.extend([source, target])
        return full_cmd

    else:
        # Proceed with SCP
        try:
            binary = os.environ["SCP_BINARY"]
        except KeyError:
            if not IS_WIN:
                binary = (
                    subprocess.check_output("which scp", shell=True)
                    .decode(sys.stdout.encoding)
                    .strip()
                )
            else:
                raise Exception("SCP binary not provided.")

        full_cmd = [binary, "-r"]
        if port is not None:
            full_cmd.extend(["-P", str(port)])
        if source.endswith(os.sep):
            # scp behaviour differs from rsync
            # TODO: test
            target = target.rsplit(os.sep, 1)[0]
        full_cmd.extend([source, target])
        return full_cmd


def link_cmd(path, link):
    """Returns link creation command."""
    return " ".join(["/bin/ln", "-sfn", shlex.quote(path), shlex.quote(link)])


def mkdir_cmd(path):
    """Return mkdir command"""
    return " ".join(["/bin/mkdir", "-p", shlex.quote(path)])


def rm_cmd(path):
    """Return rm command"""
    return " ".join(["/bin/rm", "-rf", shlex.quote(path)])


def filepath_exist_cmd(path):
    """Checks if filepath exists."""
    return " ".join(["/bin/test", "-e", shlex.quote(path)])


def paramiko_ssh_client(hostname, **paramiko_config):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
    client.connect(hostname=hostname, **paramiko_config)
    return client


def paramiko_execute_remote(
    client,
    cmd,
    label=None,
    check=True,
    logger=None,
    env=None,
):
    if not logger:
        logger = TESTPLAN_LOGGER

    if isinstance(cmd, list):
        cmd = [str(a) for a in cmd]
        # for logging, easy to copy and execute
        cmd_string = " ".join(map(shlex.quote, cmd))
    else:
        cmd_string = cmd

    if env:
        # TODO: sshd usually doesn't accept most envs, we need to embed them in cmd str
        env_str = " ".join(
            f"{k}={shlex.quote(str(v))}" for k, v in env.items()
        )
        cmd_string = f"{env_str} {cmd_string}"

    if not label:
        label = hash(cmd_string) % 1000

    logger.debug("Executing command [%s]: '%s'", label, cmd_string)
    start_time = time.time()

    _0, _1, _2 = client.exec_command(cmd_string)
    retcode = _1.channel.recv_exit_status()
    stdout = _1.read().decode()
    stderr = _2.read().decode()
    elapsed = time.time() - start_time

    if retcode != 0:
        logger.debug(
            "Failed executing command [%s] after %.2f sec.", label, elapsed
        )
        if check:
            raise RuntimeError(
                f"Command '{cmd_string}' returned with non-zero exit code {retcode},\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}\n"
            )
    else:
        logger.debug("Command [%s] finished in %.2f sec", label, elapsed)

    return retcode, stdout, stderr
