"""Unit tests for the path utilities."""
import os

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
