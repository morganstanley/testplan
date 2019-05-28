"""Dirs/file path utilities."""

import os
import errno
import shutil
import getpass
import contextlib
import tempfile

from .strings import slugify

from testplan.vendor.tempita import Template

VAR_TMP = os.path.join(os.sep, 'var', 'tmp')


def fix_home_prefix(path):
    """
    Try to replace a real path (/a/path/user) with a symlink
    path (/symlink/path/user), with clue from userhome and current working
    directory.
    """

    path = path.replace(' ', r'\ ')
    userhome = os.path.expanduser('~')
    realhome = os.path.realpath(userhome)
    if path.startswith(realhome):
        return path.replace(realhome, userhome)

    pwd = os.environ.get('PWD')
    if pwd:
        realpwd = os.path.realpath(pwd)
        if path.startswith(realpwd):
            return path.replace(realpwd, pwd)

    return path


def module_abspath(module):
    """Returns file path of a python module."""
    return fix_home_prefix(module.__file__)


def pwd():
    """Working directory path."""
    return fix_home_prefix(os.getcwd())


def workspace_root():
    """Default workspace root is the current directory."""
    return pwd()


def default_runpath(entity):
    """
    Returns default runpath for an
    :py:class:`Entity <testplan.common.entity.base.Entity>` object.
    """
    # On POSIX systems, use /var/tmp in preference to /tmp for the runpath if it
    # exists.
    if os.name == 'posix' and os.path.exists(VAR_TMP):
        runpath_prefix = VAR_TMP
    else:
        runpath_prefix = tempfile.gettempdir()

    runpath = os.path.join(
        runpath_prefix, getpass.getuser(), 'testplan', slugify(entity.uid()))
    return runpath

@contextlib.contextmanager
def change_directory(directory):
    """
    A context manager that changes working directory and returns to original on
    exit.

    :param directory: Directory to change into.
    :type directory: ``str``
    """
    old_directory = os.getcwd()
    os.chdir(directory)
    if 'PWD' in os.environ:
        os.environ['PWD'] = directory
    try:
        yield
    finally:
        os.chdir(old_directory)
        if 'PWD' in os.environ:
            os.environ['PWD'] = old_directory


def makedirs(path):
    """
    A trivial wrapper for os.makedirs that doesn't raise
    when the directory already exists.

    :param path: Path to be created.
    :type path: ``str``
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        if not os.path.isdir(path):
            raise


def makeemptydirs(path):
    """
    Make an empty directory at a location.

    :param path: Path to be created.
    :type path: ``str``
    """
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            os.remove(path)
        except OSError:
            pass
    makedirs(path)


class StdFiles(object):
    """
    stderr and stdout file creation and management
    """
    def __init__(self, directory):
        """
        Create files and initialize fds
        """
        self.err_path = os.path.join(directory, 'stderr')
        self.out_path = os.path.join(directory, 'stdout')

        self.err = open(self.err_path, 'w')
        self.out = open(self.out_path, 'w')

    def open_out(self):
        """Open the stdout file with read access"""
        return open(self.out_path, 'r')

    def open_err(self):
        """Open the stderr file with read access"""
        return open(self.err_path, 'r')

    def close(self):
        """
        Close fds
        """
        self.err.close()
        self.out.close()


def instantiate(template, values, destination):
    """
    Instantiate a templated file with a set of values and
    place it in a target destination.

    :param template: the path to the templated file
    :type template: ``str``
    :param values: the context dict to be used when
                   instantiating the templated file
    :type values: ``dict``
    :param destination: the path to the destination directory/file to
                        write the instantiated templated file to
    :type destination: ``str``

    :return: ``None``
    :rtype: ``NoneType``
    """
    makedirs(os.path.dirname(destination))
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(template))
    with open(destination, 'w') as target:
        with open(template, 'r') as source:
            try:
                tmplt = Template(source.read())
                target.write(tmplt.substitute(values))
            except Exception as exc:
                raise Exception(
                    'On reading/writing template: {} - of file {}'.format(
                        exc, template))


def unique_name(name, names):
    """
    Takes a file or directory name and set of other file or directory names

    Returns a new unique name if it exists already in the specifed set,
    or the original if it does not exist in the set.

    The names set is unaffected.
    The new name is generated by appending a suffix before the
    extention (if any).

    For example ``'stdout.log'`` becomes ``'stdout-1.log'``,
    then ``'stdout-2.log'``, ``'stdout-3.log'``, etc.

    :param name: A file or directory name (not path)
                that may or may not be unique
    :type name: ``str``
    :param names: A set of names (not paths), not modified by this function
    :type names: ``set`` of ``str``

    :return: Either the same, or a new unique name
    :rtype: ``str``
    """
    suffix = ''
    orig_name = name
    while name in names:
        if suffix == '':
            suffix = '-1'
        else:
            suffix = "-{}".format(int(suffix[1:]) + 1)
        base, ext = os.path.splitext(orig_name)
        name = "{base}{suffix}{ext}".format(base=base, suffix=suffix, ext=ext)
    return name


def to_posix_path(from_path):
    """
    :param: File path, in local OS format.
    :return: POSIX-formatted path.
    """
    return '/'.join(from_path.split(os.sep))


def is_subdir(child, parent):
    """
    Check whether "parent" is a sub-directory of "child".

    :param child: Child path.
    :param parent: Parent directory to check against.
    :return: True if child is a sub-directory of the parent.
    """
    return child.startswith(parent)
