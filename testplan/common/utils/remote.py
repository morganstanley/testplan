"""Remote execution utilities."""

import os
import platform
import socket
import sys
import getpass
import subprocess

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


def copy_cmd(source, target, exclude=None, port=None, deref_links=False):
    """Returns remote copy command."""

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
            full_cmd.extend(["-P", port])
        full_cmd.extend([source, target])
        return full_cmd


def link_cmd(path, link):
    """Returns link creation command."""
    return " ".join(["ln", "-sfn", path, link])


def mkdir_cmd(path):
    """Return mkdir command"""
    return " ".join(["/bin/mkdir", "-p", path])


def rm_cmd(path):
    """Return rm command"""
    return " ".join(["/bin/rm", "-rf", path])


def filepath_exist_cmd(path):
    """Checks if filepath exists."""
    return " ".join(["test", "-e", path])
