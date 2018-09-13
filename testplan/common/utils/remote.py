"""Remote execution utilities."""

import os
import getpass
import subprocess


def ssh_cmd(host, command):
    """Returns ssh command."""
    try:
        binary = os.environ['SSH_BINARY']
    except KeyError:
        if os.name != 'nt':
            binary = bytes(subprocess.check_output(
                'which ssh', shell=True).strip()).decode('UTF-8')
        else:
            raise Exception('SSH binary not provided.')
    return [binary, '{}@{}'.format(getpass.getuser(), host), command]


def copy_cmd(source, target, exclude=None):
    """Returns remote copy command."""
    if os.environ.get('RSYNC_BINARY'):
        cmd = [os.environ['RSYNC_BINARY'], '-r']
        if exclude is not None:
            for item in exclude:
                cmd.extend(['--exclude', item])
        cmd.extend([source, target])
        return cmd
    # Proceed with SCP.
    try:
        binary = os.environ['SCP_BINARY']
    except:
        if os.name != 'nt':
            binary = bytes(subprocess.check_output(
                'which scp', shell=True).strip()).decode('UTF-8')
        else:
            raise Exception('SCP binary not provided.')
    return [binary, '-r', source, target]


def remote_filepath_exists(ssh_cmd, host, path):
    """Checks if filepath exists."""
    return ssh_cmd(host, 'test -e {}'.format(path))
