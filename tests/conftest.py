"""Shared PyTest fixtures."""

import os
import shutil
import sys
import tempfile
from logging import Logger, INFO
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import pytest

import testplan
from testplan import TestplanMock
from testplan.common.utils.path import VAR_TMP
from testplan.common.utils import observability
from testplan.common.utils.observability import RootTraceIdGenerator, Tracing


# Testplan and various drivers have a `runpath` attribute in their config
# and intermediate files will be placed under that path during running.
# In PyTest we can invoke fixtures such as `runpath`, `runpath_module` and
# `mockplan` so that a temporary `runpath` is generated. In order to easily
# collect the output an environment variable `TEST_ROOT_RUNPATH` can be set,
# it will be the parent directory of all those temporary `runpath`.


def _generate_runpath():
    """
    Generate a temporary directory unless specified by environment variable.
    """
    if os.environ.get("TEST_ROOT_RUNPATH"):
        dir = tempfile.TemporaryDirectory(dir=os.environ["TEST_ROOT_RUNPATH"])
        yield dir.name
        shutil.rmtree(dir.name, ignore_errors=True)
    else:
        parent_runpath = (
            VAR_TMP if os.name == "posix" and os.path.exists(VAR_TMP) else None
        )
        # The path will be automatically removed after the test
        dir = tempfile.TemporaryDirectory(dir=parent_runpath)
        yield dir.name
        shutil.rmtree(dir.name, ignore_errors=True)


# For `runpath` series fixtures, We were originally using a pytest builtin
# fixture called `tmp_path`, which will create a path in a form like:
# "/tmp/pytest-of-userid/pytest-151/test_sub_pub_unsub0", but it has a known
# issue: https://github.com/pytest-dev/pytest/issues/5456


@pytest.fixture(scope="function")
def runpath():
    """
    Return a temporary runpath for testing (function level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="class")
def runpath_class():
    """
    Return a temporary runpath for testing (class level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="module")
def runpath_module():
    """
    Return a temporary runpath for testing (module level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="function")
def mockplan(runpath):
    """
    Return a temporary TestplanMock for testing. Some components need a
    testplan as parent for getting runpath and configuration.
    """
    yield TestplanMock("plan", runpath=runpath)


@pytest.fixture(scope="session")
def repo_root_path():
    """
    Return the path to the root of the testplan repo as a string. Useful
    for building paths to specific files/directories in the repo without
    relying on the current working directory or building a relative path from
    a different known filepath.
    """
    # This file is at tests/conftest.py. It should not be moved, since it
    # defines global pytest fixtures for all tests.
    return os.path.join(os.path.dirname(__file__), os.pardir)


@pytest.fixture(scope="session")
def root_directory(pytestconfig):
    """
    Return the root directory of pyTest config as a string.
    """
    return str(pytestconfig.rootdir)


class RotatingLogger(Logger):
    def __init__(self, path: str, name: str) -> None:
        super().__init__(name)
        self.path = path
        self.handler = RotatingFileHandler(
            path, maxBytes=10 * 1024, backupCount=5
        )
        self.addHandler(self.handler)

    @property
    def pattern(self):
        return f"{self.path}*"

    def doRollover(self):
        self.handler.doRollover()


@pytest.fixture
def rotating_logger(runpath):
    logpath = os.path.join(runpath, "test.log")
    logger = RotatingLogger(logpath, "TestLogger")
    yield logger

    logger.handler.close()


@pytest.fixture
def captplog(caplog):
    from testplan.common.utils.logger import TESTPLAN_LOGGER

    caplog.set_level(INFO)
    TESTPLAN_LOGGER.addHandler(caplog.handler)
    yield caplog
    TESTPLAN_LOGGER.removeHandler(caplog.handler)


# --- Shared Observability Fixtures ---


@pytest.fixture(scope="session")
def session_provider_exporter():
    """
    Session-scoped OpenTelemetry provider and in-memory exporter.
    Sets the global tracer provider once per session.
    Also resets the Testplan tracing singleton before use to avoid stale state.
    """
    pytest.importorskip("opentelemetry")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    from opentelemetry import trace

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Save the original provider (could be None or already set by --otel-traces).
    original_provider = trace.get_tracer_provider()

    # Forcefully set the test provider for this session.
    trace._TRACER_PROVIDER = provider

    yield provider, exporter
    trace._TRACER_PROVIDER = original_provider
    provider.shutdown()


@pytest.fixture
def test_exporter(session_provider_exporter):
    """
    Function-scoped fixture that provides a clean tracing environment per test.
    Patches Tracing._setup to use the session provider instead of reading env vars.
    """
    from opentelemetry import trace

    provider, exporter = session_provider_exporter

    existing_tracing = observability.tracing

    # Capture original tracing state to restore after the test.
    original_tracing_enabled = getattr(
        existing_tracing, "_tracing_enabled", False
    )
    original_root_context = getattr(
        existing_tracing, "_root_context", {}
    ).copy()
    original_tracer = getattr(existing_tracing, "_tracer", None)
    original_tracer_provider = getattr(
        existing_tracing, "_tracer_provider", None
    )
    fixture_id_generator = provider.id_generator

    def mock_setup(traceparent=None):
        if traceparent:
            existing_tracing._root_context = {"traceparent": traceparent}

        existing_tracing._tracer_provider = provider
        existing_tracing._tracer_provider.id_generator = RootTraceIdGenerator(
            existing_tracing
        )
        existing_tracing._tracer = trace.get_tracer("testplan_tracer")
        existing_tracing._tracing_enabled = True

    existing_tracing._setup = mock_setup
    existing_tracing._tracing_enabled = False

    yield exporter
    exporter.clear()

    existing_tracing._tracing_enabled = original_tracing_enabled
    existing_tracing._root_context = original_root_context
    existing_tracing._tracer = original_tracer
    existing_tracing._tracer_provider = original_tracer_provider
    provider.id_generator = fixture_id_generator


@pytest.fixture
def unit_test_tracing(session_provider_exporter):
    from opentelemetry import trace

    provider, exporter = session_provider_exporter
    fresh_tracing = Tracing()

    def mock_setup(traceparent=None):
        if traceparent:
            fresh_tracing._root_context = {"traceparent": traceparent}

        fresh_tracing._tracer_provider = provider
        fresh_tracing._tracer = trace.get_tracer("testplan_tracer")
        fresh_tracing._tracing_enabled = True

    fresh_tracing._setup = mock_setup

    yield fresh_tracing, exporter

    exporter.clear()
