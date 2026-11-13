"""Unit tests for the path utilities."""

import subprocess
import re
import os
import threading
import time
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
    original = os.getcwd()
    targets = [
        os.path.realpath(str(tmpdir.mkdir(name))) for name in ("a", "b")
    ]

    def racing_worker(target, barrier):
        barrier.wait()
        with path.change_directory(target):
            # Widen the window for another thread to chdir concurrently.
            time.sleep(0.001)
            return os.path.realpath(os.getcwd())

    try:
        for _ in range(50):
            barrier = threading.Barrier(2)
            with ThreadPoolExecutor(max_workers=2) as executor:
                seen = list(
                    executor.map(racing_worker, targets, [barrier, barrier])
                )
            assert seen == targets, (
                "another thread changed directory concurrently"
            )
            assert os.getcwd() == original, (
                "did not return to original directory"
            )
    finally:
        # Keep a failed restore from leaking into later tests.
        os.chdir(original)


def test_change_directory_rlock(tmpdir):
    # as long as this test doesn't hang
    cwd = os.getcwd()
    with path.change_directory(str(tmpdir)):
        with path.change_directory(cwd):
            pass
