import os
import tempfile
from collections import defaultdict

import pytest
from pytest_test_filters import skip_on_windows

from testplan.runners.pools.process import ProcessPool
from testplan.testing.base import ProcessRunnerTest
from testplan.testing.multitest.driver.base import Driver


@pytest.fixture
def named_temp_file():
    tmp_d = tempfile.mkdtemp()
    tmp_f = os.path.join(tmp_d, "tmp_file")
    with open(tmp_f, "w"):
        pass
    try:
        yield tmp_f
    finally:
        os.remove(tmp_f)
        os.rmdir(tmp_d)


class MyDriver(Driver):
    def __init__(self, temp_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_file = temp_file

    def pre_start(self):
        with open(self.temp_file, "a") as f:
            f.write(f"{self.name}_PRE\n")
        super().pre_start()

    def post_start(self):
        with open(self.temp_file, "a") as f:
            f.write(f"{self.name}_POST\n")
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
    def __init__(self, temp_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_file = temp_file

    def __missing__(self, key):
        self[key] = MyDriver(self.temp_file, key)
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
def test_testing_environment(mockplan, driver_dependencies, named_temp_file):

    drivers = DriverGeneratorDict(named_temp_file)
    dependency = defaultdict(list)
    predicates = list()
    for side_a, side_b in driver_dependencies:
        dependency[drivers[side_a]].append(drivers[side_b])
        predicates.append(
            lambda line_of: line_of[f"{drivers[side_a].name}_POST"]
            < line_of[f"{drivers[side_b].name}_PRE"]
        )

    mockplan.add_resource(ProcessPool(name="I'm not local."))
    mockplan.schedule(
        target=DummyTest(
            name="MyTest",
            binary=binary_path,
            environment=list(drivers.values()),
            dependency=dependency,
        ),
        resource="I'm not local.",
    )
    assert mockplan.run().success is True

    with open(named_temp_file, "r") as f:
        lines = f.read().splitlines()

    for pred in predicates:
        assert pred(dict(zip(lines, range(len(lines)))))
