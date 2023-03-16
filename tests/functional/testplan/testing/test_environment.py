import os
import time
from collections import defaultdict

import pytest
from pytest_test_filters import skip_on_windows

from testplan.testing.base import ProcessRunnerTest
from testplan.testing.multitest.driver.base import Driver


class MyDriver(Driver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pre_start_time = None
        self.post_start_time = None

    def pre_start(self):
        self.pre_start_time = time.time()
        super().pre_start()

    def post_start(self):
        self.post_start_time = time.time()
        super().post_start()


class DummyTest(ProcessRunnerTest):
    def process_test_data(self, _):
        return []

    def read_test_data(self):
        pass


binary_path = os.path.join(
    os.path.dirname(__file__), "fixtures", "base", "passing", "test.sh"
)


class DriverGeneratorDict(dict):
    def __missing__(self, key):
        self[key] = MyDriver(key)
        return self[key]


@skip_on_windows(reason="Bash files skipped on Windows.")
@pytest.mark.parametrize(
    "driver_dependencies",
    [
        [("a", "b")],
        [("a", "b"), ("b", "c"), ("a", "c")],
        [("a", "b"), ("c", "d"), ("a", "d"), ("c", "b")],
    ],
)
def test_testing_environment(mockplan, driver_dependencies):

    drivers = DriverGeneratorDict()
    dependency = defaultdict(list)
    predicates = list()
    for side_a, side_b in driver_dependencies:
        dependency[drivers[side_a]].append(drivers[side_b])
        predicates.append(
            lambda: drivers[side_a].post_start_time
            < drivers[side_b].pre_start_time
        )

    mockplan.add(
        DummyTest(
            name="MyTest",
            binary=binary_path,
            environment=list(drivers.values()),
            dependency=dependency,
        )
    )
    assert mockplan.run().run is True
    for pred in predicates:
        assert pred()
