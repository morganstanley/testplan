"""Module containing SSH client functionality for remote operations."""

import os
import time
import logging
import paramiko
import getpass
from contextlib import contextmanager
from typing import List, Dict

from testplan.common.utils.timing import retry_until_timeout
from testplan.common.utils.logger import TESTPLAN_LOGGER

logger = logging.getLogger(__name__)

DEFAULT_PARAMIKO_CONFIG = {
    "username": getpass.getuser(),
}


class SSHClient:
    """
    SSH client for remote operations including file transfers and command execution.
    Wraps paramiko functionality in a convenient interface.
    """

    def __init__(
        self,
        host,
        port: int = 22,
        logger=None,
        **args,
    ):
        """
        Initialize the SSH client.

        :param host: Host to connect to
        :type host: ``str``
        :param port: Port to connect to
        :type port: ``int``
        :param user: Username to connect with
        :type user: ``str``
        :param password: Password to use for authentication
        :type password: ``str`` or ``NoneType``
        :param key_path: Path to private key file to use for authentication
        :type key_path: ``str`` or ``NoneType``
        """
        self.host = host
        self.port = port
        self.logger = logger or TESTPLAN_LOGGER

        self.paramiko_args = DEFAULT_PARAMIKO_CONFIG
        self.paramiko_args.update(
            {
                "hostname": self.host,
                "port": self.port,
            }
        )
        self.paramiko_args.update(args)

        self._ssh_client = None
        self._sftp_client = None

    def connect(self):
        """
        Establish an SSH connection.

        :return: Self for method chaining
        :rtype: ``SSHClient``
        """
        if self._ssh_client is not None:
            self.logger.warning("SSH connection already established")
            return self._ssh_client

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())

        ssh_client.connect(**self.paramiko_args)
        self.logger.debug(
            "Connected to %s@%s:%s",
            self.paramiko_args["username"],
            self.paramiko_args["hostname"],
            self.paramiko_args["port"],
        )

        self._ssh_client = ssh_client
        return self._ssh_client

    def exec_command(
        self,
        cmd: str | List[str],
        label: str = None,
        check: bool = True,
        env: Dict = None,
        timeout: int = 30,
    ):
        """
        Run a command on the remote host.

        :param cmd: Command to execute (either a string or list of arguments)
        :type cmd: ``str`` or ``List[str]``
        :param label: Label for identifying the command in logs (defaults to hash of command)
        :type label: ``str`` or ``NoneType``
        :param check: If True, raises exception when command fails
        :type check: ``bool``
        :param env: Environment variables to set for the command
        :type env: ``Dict`` or ``NoneType``
        :param timeout: Timeout for command execution in seconds
        :type timeout: ``int``
        :return: Tuple of (exit_code, stdout_str, stderr_str)
        :rtype: ``tuple`` of (``int``, ``str``, ``str``)
        :raises: ``RuntimeError`` if command fails and check is True
        """
        if not self._ssh_client:
            self.connect()

        if isinstance(cmd, list):
            cmd = [str(a) for a in cmd]
            # for logging, easy to copy and execute
            cmd_string = " ".join(map(shlex.quote, cmd))
        else:
            cmd_string = cmd

        if not label:
            label = hash(cmd_string) % 1000

        self.logger.debug(
            "ssh_client executing command [%s]: '%s'",
            label,
            cmd_string,
        )
        start_time = time.time()

        _, stdout, stderr = self._ssh_client.exec_command(
            command=cmd_string,
            timeout=timeout,
            environment=env,
        )
        elapsed = time.time() - start_time
        exit_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode("utf-8").strip()
        stderr_str = stderr.read().decode("utf-8").strip()

        if exit_code != 0:
            self.logger.warning(
                "Failed executing command [%s] after %.2f sec.", label, elapsed
            )
            if stdout_str:
                self.logger.debug("Stdout:\n%s", stdout_str)
            if stderr_str:
                self.logger.debug("Stderr:\n%s", stderr_str)
            if check:
                raise RuntimeError(
                    f"Command '{cmd_string}' failed with exit code {exit_code}."
                )
        else:
            self.logger.debug(
                "Command [%s] executed successfully in %.2f sec.",
                label,
                elapsed,
            )

        return exit_code, stdout_str, stderr_str

    def open_sftp(self):
        """
        Open an SFTP session.

        :return: SFTP client object
        :rtype: ``paramiko.sftp_client.SFTPClient``
        """

        if self._sftp_client is not None:
            self.logger.warning("SFTP session already open")
            return self._sftp_client

        if not self._ssh_client:
            self.connect()

        self._sftp_client = self._ssh_client.open_sftp()
        self.logger.debug("Opened SFTP session to %s:%s", self.host, self.port)
        return self._sftp_client

    def listdir_iter(self, path):
        """
        List files in a directory on the remote host.

        :param path: Path to the directory to list
        :type path: ``str``
        :return: Generator yielding file names in the directory
        :rtype: ``generator`` of ``str``
        """
        if not self._sftp_client:
            self.open_sftp()

        self.logger.debug("Listing directory: %s", path)
        return self._sftp_client.listdir_iter(path)

    def open_file(self, path, mode):
        """
        Open a file on the remote host using SFTP.

        :param path: Path to the file to open
        :type path: ``str``
        :param mode: Mode in which to open the file (e.g., 'r', 'w', 'rb')
        :type mode: ``str``
        :return: File object for the remote file
        :rtype: ``paramiko.sftp_file.SFTPFile``
        """
        if not self._sftp_client:
            self.open_sftp()

        self.logger.debug("Opening remote file: %s in mode %s", path, mode)
        return self._sftp_client.open(path, mode)

    def close(self):
        """
        Close the SSH and SFTP connections.

        :return: None
        """
        if self._sftp_client:
            self._sftp_client.close()
            self._sftp_client = None
            self.logger.debug("Closed SFTP session")

        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
            self.logger.debug("Closed SSH connection")
