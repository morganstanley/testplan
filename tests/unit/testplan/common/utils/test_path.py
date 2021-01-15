"""Unit tests for the path utilities."""
import os
import subprocess
import re

import pytest

from testplan.common.utils import path


def test_tempdir():
    """
    Test the TemporaryDirectory context manager.

    On python 3 this is just tempfile.TemporaryDirectory so it's not very
    interesting, but for python 2 we use our home baked backport, so it should
    have a test!
    """
    with path.TemporaryDirectory() as tmpdir:
        assert os.path.isdir(tmpdir)

    # Path no longer exists outside of context mgr.
    assert not os.path.exists(tmpdir)


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
