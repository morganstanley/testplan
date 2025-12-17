"""Functional tests for archive_runpath feature."""

from pytest_test_filters import skip_on_windows

pytestmark = skip_on_windows(
    reason="Subprocess based approach is problematic on windows."
)

import os
import tarfile
import tempfile

import pytest
import zstandard as zstd

from testplan import TestplanMock
from testplan.common.utils.testing import argv_overridden
from testplan.testing import multitest


@multitest.testsuite
class BasicSuite:
    """Basic test suite with both passing and failing tests."""

    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, description="Passing test")

    @multitest.testcase
    def test_fail(self, env, result):
        result.equal(1, 2, description="Failing test")


@multitest.testsuite
class PassingOnlySuite:
    """Test suite with only passing tests."""

    @multitest.testcase
    def test_pass_1(self, env, result):
        result.equal(1, 1, description="First passing test")

    @multitest.testcase
    def test_pass_2(self, env, result):
        result.equal(2, 2, description="Second passing test")


@multitest.testsuite
class ErrorSuite:
    """Test suite that raises an error."""

    @multitest.testcase
    def test_error(self, env, result):
        raise RuntimeError("Simulated error in test")


def test_archive_runpath_cmdline_option(runpath):
    """Test archive_runpath via command line argument."""
    archive_dir = os.path.join(runpath, "archives")
    os.makedirs(archive_dir)

    with argv_overridden(
        "--archive-runpath",
        archive_dir,
        "--runpath",
        runpath,
    ):
        plan = TestplanMock(name="TestPlan", parse_cmdline=True)
        plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
        result = plan.run()

        # Test should fail due to failing assertion
        assert result.report.failed

        # Archive should be created
        archive_files = [
            f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
        ]
        assert len(archive_files) == 1


def test_archive_created_on_test_failure(runpath):
    """Test that archive is created when tests fail."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="FailingTest", suites=[BasicSuite()]))
    result = plan.run()

    # Verify test failed
    assert result.report.failed

    # Verify archive was created
    assert os.path.exists(archive_dir)
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1

    # Verify archive contains expected content
    archive_path = os.path.join(archive_dir, archive_files[0])
    assert os.path.getsize(archive_path) > 0


def test_archive_not_created_on_test_pass(runpath):
    """Test that archive is NOT created when all tests pass."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(
        multitest.MultiTest(name="PassingTest", suites=[PassingOnlySuite()])
    )
    result = plan.run()

    # Verify test passed
    assert result.report.passed

    # Verify no archive was created
    if os.path.exists(archive_dir):
        archive_files = [
            f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
        ]
        assert len(archive_files) == 0


def test_archive_created_on_test_error(runpath):
    """Test that archive is created when tests have errors."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="ErrorTest", suites=[ErrorSuite()]))
    result = plan.run()

    # Verify test had error (exception causes failure)
    assert result.report.failed

    # Verify archive was created
    assert os.path.exists(archive_dir)
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1


def test_archive_contains_runpath_contents(runpath):
    """Test that archive contains all runpath contents."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
    result = plan.run()

    # Get the archive
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1

    archive_path = os.path.join(archive_dir, archive_files[0])

    # Extract and verify contents
    with open(archive_path, "rb") as f:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(f) as decompressor:
            with tarfile.open(fileobj=decompressor, mode="r|") as tar:
                member_names = [m.name for m in tar.getmembers()]
                # Check that runpath base name is in the archive structure
                assert any(
                    os.path.basename(runpath) in name for name in member_names
                )

                # Check for testplan log file
                assert any("testplan.log" in name for name in member_names)


def test_archive_filename_format(runpath):
    """Test that archive filename follows expected format."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
    result = plan.run()

    # Get the archive
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1

    archive_filename = archive_files[0]

    # Verify filename format: <runpath_basename>_<timestamp>.tar.zst
    assert archive_filename.endswith(".tar.zst")
    assert os.path.basename(runpath) in archive_filename
    # Should contain timestamp (format: YYYYMMDD-HHMMSS)
    assert "_" in archive_filename


def test_archive_with_multiple_multitests(runpath):
    """Test archiving with multiple MultiTests."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    # Add multiple tests, one will fail
    plan.add(multitest.MultiTest(name="Test1", suites=[PassingOnlySuite()]))
    plan.add(
        multitest.MultiTest(name="Test2", suites=[BasicSuite()])
    )  # Has failure
    plan.add(multitest.MultiTest(name="Test3", suites=[PassingOnlySuite()]))

    result = plan.run()

    # Overall plan should fail due to Test2
    assert result.report.failed

    # Archive should be created
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1


def test_archive_without_option_no_archive(runpath):
    """Test that no archive is created when option is not specified."""
    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        # archive_runpath not specified
    )

    plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
    result = plan.run()

    # No archives directory should be created
    archive_dir = os.path.join(runpath, "archives")
    assert not os.path.exists(archive_dir)


def test_archive_compression_valid(runpath):
    """Test that created archive is a valid zstd compressed tar file."""
    archive_dir = os.path.join(runpath, "archives")

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
    result = plan.run()

    # Get the archive
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    archive_path = os.path.join(archive_dir, archive_files[0])

    # Verify it's a valid zstd file
    try:
        with open(archive_path, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(f) as decompressor:
                # Try to read first few bytes to verify decompression works
                decompressor.read(1024)
    except Exception as e:
        pytest.fail(f"Archive is not a valid zstd file: {e}")

    # Verify it's a valid tar file (after decompression)
    try:
        with open(archive_path, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(f) as decompressor:
                with tarfile.open(fileobj=decompressor, mode="r|") as tar:
                    # Just iterate to verify tar structure
                    list(tar.getmembers())
    except Exception as e:
        pytest.fail(f"Archive is not a valid tar file: {e}")


def test_archive_directory_creation(runpath):
    """Test that archive directory is automatically created if it doesn't exist."""
    archive_dir = os.path.join(runpath, "some", "nested", "archives")
    # Don't create the directory beforehand

    plan = TestplanMock(
        name="TestPlan",
        runpath=runpath,
        archive_runpath=archive_dir,
    )

    plan.add(multitest.MultiTest(name="Test", suites=[BasicSuite()]))
    result = plan.run()

    # Archive directory should be created
    assert os.path.exists(archive_dir)
    assert os.path.isdir(archive_dir)

    # Archive should be created
    archive_files = [
        f for f in os.listdir(archive_dir) if f.endswith(".tar.zst")
    ]
    assert len(archive_files) == 1
