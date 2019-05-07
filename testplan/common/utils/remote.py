"""Remote execution utilities."""

import os
import sys
import getpass
import subprocess


def ssh_cmd(ssh_cfg, command):
    """Returns ssh command."""
    try:
        binary = os.environ['SSH_BINARY']
    except KeyError:
        if os.name != 'nt':
            binary = subprocess.check_output(
                'which ssh', shell=True).decode(sys.stdout.encoding).strip()
        else:
            raise Exception('SSH binary not provided.')

    cmd = [binary]

    if ssh_cfg.get('port'):
        cmd.extend(['-p', ssh_cfg['port']])

    cmd.append('{}@{}'.format(getpass.getuser(), ssh_cfg['host']))
    cmd.append(command)

    return cmd


def copy_cmd(source, target, exclude=None, port=None, deref_links=False):
    """Returns remote copy command."""
    if os.environ.get('RSYNC_BINARY'):
        cmd = [os.environ['RSYNC_BINARY'], '-r']
        cmd.append('-l' if deref_links else '-L')

        if exclude is not None:
            for item in exclude:
                cmd.extend(['--exclude', item])

        if port is not None:
            # Add '-e "ssh -p "' option to rsync command
            ssh = '{} -p {}'.format(
                os.environ['SSH_BINARY'],
                port)
            cmd.extend(['-e', ssh])

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
    cmd = [binary, '-r']
    if port is not None:
        cmd.extend(['-P', port])
    cmd.extend([source, target])
    return cmd


def link_cmd(path, link):
    """Returns link creation command."""
    return ['ln', '-sfn', path, link]


def remote_filepath_exists(ssh_cmd, ssh_cfg, path):
    """Checks if filepath exists."""
    return ssh_cmd(ssh_cfg, 'test -e {}'.format(path))

