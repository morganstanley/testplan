from multiprocessing.pool import ThreadPool
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser
from pathlib import Path
import pytest

from testplan.testing.bdd.step_registry import StepRegistry


@pytest.fixture
def features_dir() -> Path:
    return Path(__file__).parent / "features"


def test_parallel_featurefile_parsing(features_dir):
    pool = ThreadPool(processes=2)

    async_result_1 = pool.apply_async(
        BDDTestSuiteFactory,
        kwds={
            "features_path": features_dir / "feature1",
            "default_parser": SimpleParser,
        },
    )
    async_result_2 = pool.apply_async(
        BDDTestSuiteFactory,
        kwds={
            "features_path": features_dir / "feature2",
            "default_parser": SimpleParser,
        },
    )

    pool.close()
    pool.join()

    factory_1 = async_result_1.get()
    factory_2 = async_result_2.get()

    assert factory_1.features
    assert factory_2.features


def get_testcase_tags(suite):
    return [
        getattr(suite, case).__tags__["simple"] for case in suite.__testcases__
    ]


def test_labels(features_dir):
    factory = BDDTestSuiteFactory(features_dir / "labels")
    suite = factory.create_suites()[0]

    assert suite.__tags__
    assert "simple" in suite.__tags__
    assert suite.__tags__["simple"] == {"fast", "has_outline", "KNOWN_TO_FAIL"}

    tags = get_testcase_tags(suite)

    # KNOWN_TO_FAIL reason is stripped TP_EXECUTION_GROUP is not in labels

    assert tags == [
        {"single", "KNOWN_TO_FAIL"},
        {"parametrized", "positive"},
        {"parametrized", "positive"},
        {"parametrized", "positive"},
        {"parametrized", "negative", "KNOWN_TO_FAIL"},
        {"parametrized", "negative", "KNOWN_TO_FAIL"},
        {"parametrized", "negative", "KNOWN_TO_FAIL"},
    ]


def test_import_steps(features_dir):
    registry = StepRegistry()

    steps_dir = features_dir / "import_steps"

    registry.load_steps(steps_dir / "steps1.py", SimpleParser)
    assert len(registry.func_map) == 4
    match_strings = [
        parser.parser._format for parser in registry.func_map.keys()
    ]
    assert match_strings == ["common", "util", "common2", "steps1"]

    registry.load_steps(steps_dir / "steps2.py", SimpleParser)
    assert len(registry.func_map) == 8
    match_strings = [
        parser.parser._format for parser in registry.func_map.keys()
    ]
    assert match_strings == [
        "common",
        "util",
        "common2",
        "steps1",
        "common",
        "util",
        "common2",
        "steps2",
    ]


def test_import_steps_concurrent(features_dir):
    pool = ThreadPool(processes=2)
    steps_dir = features_dir / "import_steps"
    registry = StepRegistry()

    pool.apply_async(
        registry.load_steps, (steps_dir / "steps1.py", SimpleParser)
    )
    pool.apply_async(
        registry.load_steps, (steps_dir / "steps2.py", SimpleParser)
    )

    pool.close()
    pool.join()

    assert len(registry.func_map) == 8
    match_strings = [
        parser.parser._format for parser in registry.func_map.keys()
    ]
    # we expect the same set as in non concurrent but the orders are not defined
    assert set(match_strings) == {
        "common",
        "util",
        "common2",
        "steps1",
        "common",
        "util",
        "common2",
        "steps2",
    }
