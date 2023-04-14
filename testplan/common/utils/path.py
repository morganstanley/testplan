"""Dirs/file path utilities."""

import os
import errno
import shutil
import fnmatch
import getpass
import contextlib
import tempfile
import hashlib
from io import TextIOWrapper

from testplan.common.utils.context import render
from memoization import cached
from .strings import slugify

VAR_TMP = os.path.join(os.sep, "var", "tmp")


@cached
def fix_home_prefix(path):
    """
    Try to replace a real path (/a/path/user) with a symlink
    path (/symlink/path/user), with clue from userhome and current working
    directory.
    """

    userhome = os.path.expanduser("~")
    realhome = os.path.realpath(userhome)
    if path.startswith(realhome):
        return path.replace(realhome, userhome)

    pwd = os.environ.get("PWD")
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


def default_runpath(entity):
    """
    Returns default runpath for an
    :py:class:`Entity <testplan.common.entity.base.Entity>` object.
    """
    # On POSIX systems, use /var/tmp in preference to /tmp for the runpath if
    # it exists.
    if os.name == "posix" and os.path.exists(VAR_TMP):
        runpath_prefix = VAR_TMP
    else:
        runpath_prefix = tempfile.gettempdir()

    return os.path.join(
        runpath_prefix, getpass.getuser(), "testplan", slugify(entity.uid())
    )


PWD = "PWD"


@contextlib.contextmanager
def change_directory(directory):
    """
    A context manager that changes working directory and returns to original on
    exit.

    :param directory: Directory to change into.
    :type directory: ``str``
    """

    if directory:  # in case we get a None directory, do nothing
        old_directory = os.getcwd()
        old_pwd = os.environ.get(PWD, None)
        directory = fix_home_prefix(directory)
        os.chdir(directory)
        if old_pwd:
            os.environ[PWD] = directory
    try:
        yield
    finally:
        if directory:
            os.chdir(old_directory)
            if old_pwd:
                os.environ[PWD] = old_pwd
            elif PWD in os.environ:
                del os.environ[PWD]


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


def removeemptydir(path):
    """
    Remove a directory if it does exist and is empty.

    :param path: Path to be created.
    :type path: ``str``
    """
    try:
        os.rmdir(path)
    except FileNotFoundError:
        pass  # directory does not exist
    except OSError:
        pass  # not a directory or not empty


class StdFiles:
    """
    stderr and stdout file creation and management
    """

    def __init__(self, directory) -> None:
        """
        Create files and initialize fds
        """
        self.err_path = os.path.join(directory, "stderr")
        self.out_path = os.path.join(directory, "stdout")

        self.err = open(self.err_path, "w")
        self.out = open(self.out_path, "w")

    def open_out(self, mode: str = "r") -> TextIOWrapper:
        """Open the stdout file with the defined access"""
        return open(self.out_path, mode)

    def open_err(self, mode: str = "r") -> TextIOWrapper:
        """Open the stderr file with the defined access"""
        return open(self.err_path, mode)

    def close(self) -> None:
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
    with open(destination, "w") as target:
        with open(template, "r") as source:
            try:
                target.write(render(source.read(), values))
            except UnicodeDecodeError:
                shutil.copy(template, destination)
            except Exception as exc:
                raise Exception(
                    "On reading/writing template: {} - of file {}".format(
                        exc, template
                    )
                )


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
    suffix = ""
    orig_name = name
    while name in names:
        if suffix == "":
            suffix = "-1"
        else:
            suffix = "-{}".format(int(suffix[1:]) + 1)
        base, ext = os.path.splitext(orig_name)
        name = "{base}{suffix}{ext}".format(base=base, suffix=suffix, ext=ext)
    return name


def rebase_path(path, old_base, new_base):
    """
    Rebase path from old_base to new_base and convert to Linux form.
    """

    rel_path = os.path.relpath(path, old_base).split(os.sep)
    return "/".join([new_base] + rel_path)


def is_subdir(child, parent):
    """
    Check whether "parent" is a sub-directory of "child".

    :param child: Child path.
    :type child: ``str``
    :param parent: Parent directory to check against.
    :type parent: ``str``
    :return: True if child is a sub-directory of the parent.
    :rtype: ``bool``
    """

    return fix_home_prefix(os.path.abspath(child)).startswith(
        fix_home_prefix(os.path.abspath(parent))
    )


def hash_file(filepath):
    """
    Hashes the contents of a file. SHA1 algorithm is used.

    :param filepath: Path to file to hash.
    :type filepath: ``str``
    :return: Hashed value as a string
    :rtype: ``str``
    """
    HASH_BLOCKSIZE = 65536
    hasher = hashlib.sha1()

    with open(filepath, "rb") as f:
        buf = f.read(HASH_BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = f.read(HASH_BLOCKSIZE)

    return hasher.hexdigest()


def archive(path, timestamp):
    """
    Append a timestamp to an existing file's name.

    :param path: Path to a file that should be archived
    :type path: ``str``
    :param timestamp: timestamp
    :type timestamp: ``str``

    :return: path to the archived file
    :rtype: ``str``
    """
    new_path = path + timestamp
    if os.path.isfile(path):
        os.rename(path, new_path)
    return new_path


def traverse_dir(
    directory,
    topdown=True,
    ignore=None,
    only=None,
    recursive=True,
    include_subdir=True,
):
    """
    Recursively traverse all files and sub directories in a directory and
    get a list of relative paths.

    :param directory: Path to a directory that will be traversed.
    :type directory: ``str``
    :param topdown: Browse the directory in a top-down or bottom-up approach.
    :type topdown: ``bool``
    :param ignore: List of patterns to ignore  by glob style filtering.
    :type ignore: ``list``
    :param only: List of patterns to include by glob style filtering.
    :type only: ``list``
    :param recursive: Traverse directories recursively, set to False to only
        list items in top directory.
    :type recursive: ``bool``
    :param include_subdir: Include all sub directories and files if True, or
        exclude directories in the result.
    :type include_subdir: ``bool``
    :return: A list of relative file paths
    :rtype: ``list`` of ``str``
    """
    result = []
    ignore = ignore or []
    only = only or []

    def should_ignore(filename):
        """Decide if a file should be ignored by its name."""
        for pattern in ignore:
            if fnmatch.fnmatch(filename, pattern):
                return True
        if only:
            for pattern in only:
                if fnmatch.fnmatch(filename, pattern):
                    return False
            else:
                return True
        return False

    for dirpath, dirnames, filenames in os.walk(
        directory, topdown=topdown or recursive is False
    ):
        if include_subdir:
            for dname in dirnames:
                if not should_ignore(dname):
                    relpath = os.path.relpath(
                        os.path.join(dirpath, dname), directory
                    )
                    result.append(relpath)

        for fname in filenames:
            if not should_ignore(fname):
                relpath = os.path.relpath(
                    os.path.join(dirpath, fname), directory
                )
                result.append(relpath)

        if recursive is False:
            break

    return result
