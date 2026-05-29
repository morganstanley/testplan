"""Unit tests for the path utilities."""

import subprocess
import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from testplan.common.utils import path


def test_hashfile(tmpdir):
    """
    Test the hash_file() utility.

    The SHA1 algorithm is used. Check that the same hash value is returned as
    given by the sha1sum utility.
    """
    tmpfile = str(tmpdir.join("hash_me.txt"))
    with open(tmpfile, "w") as f:
        f.write("testplan\n" * 1000)

    try:
        sha_output = subprocess.check_output(
            ["sha1sum", tmpfile], universal_newlines=True
        )
        ref_sha = re.match(r"\\?([0-9a-f]+)\s+.*", sha_output).group(1)
    except OSError:
        # TODO: rewrite this with hardcoded hash
        pytest.skip("Cannot call sha1sum to generate reference SHA.")
        return

    # Check that the has produced by our hash_file utility matches the
    # reference value.
    assert path.hash_file(tmpfile) == ref_sha


def test_change_directory_thread_safe(tmpdir):

    barrier = threading.Barrier(2)

    def racing_worker():
        cwd = os.getcwd()
        barrier.wait()
        with path.change_directory(str(tmpdir)):
            pass
        probably_tmpdir = os.getcwd()
        return probably_tmpdir, cwd

    for _ in range(50):
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(racing_worker)
            future2 = executor.submit(racing_worker)
            result1 = future1.result()
            result2 = future2.result()
            assert result1[0] == result1[1], (
                "thread 1 did not return to original directory"
            )
            assert result2[0] == result2[1], (
                "thread 2 did not return to original directory"
            )


def test_change_directory_rlock(tmpdir):
    # as long as this test doesn't hang
    cwd = os.getcwd()
    with path.change_directory(str(tmpdir)):
        with path.change_directory(cwd):
            pass
