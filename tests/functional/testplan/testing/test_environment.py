import os
import tempfile
from collections import defaultdict

import pytest
from pytest_test_filters import skip_on_windows

from testplan.runners.pools.process import ProcessPool
from testplan.testing.multitest.driver.base import Driver

from .test_base import DummyTest


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


def _assert_orig_dep(env):
    assert env.__dict__["_orig_dependency"] is not None


@skip_on_windows(reason="Bash files skipped on Windows.")
@pytest.mark.parametrize(
    "driver_dependencies, use_callable",
    [
        ([], False),
        ([], True),
        ([("a", "b")], False),
        ([("a", "b"), ("b", "c"), ("a", "c")], True),
        ([("a", "b"), ("c", "d"), ("a", "d"), ("c", "b")], False),
    ],
)
def test_testing_environment(
    mockplan, named_temp_file, driver_dependencies, use_callable
):
    drivers = DriverGeneratorDict(named_temp_file)
    for k in ["a", "b"]:
        drivers[k] = MyDriver(named_temp_file, k)

    predicates = list()
    if driver_dependencies is None:
        dependencies = None
    else:
        dependencies = defaultdict(list)
        for side_a, side_b in driver_dependencies:
            dependencies[drivers[side_a]].append(drivers[side_b])
            predicates.append(
                lambda line_of: line_of[f"{drivers[side_a].name}_POST"]
                < line_of[f"{drivers[side_b].name}_PRE"]
            )

    mockplan.schedule(
        target=DummyTest(
            name="MyTest",
            binary=binary_path,
            environment=lambda: list(drivers.values())
            if use_callable
            else list(drivers.values()),
            dependencies=lambda: dependencies
            if use_callable
            else dependencies,
            after_start=_assert_orig_dep,
        ),
        resource=None,
    )
    assert mockplan.run().success is True

    for i in range(len(drivers)):
        assert (
            "lifespan" in mockplan.result.report.entries[0].children[i].timer
        )

    with open(named_temp_file, "r") as f:
        lines = f.read().splitlines()

    for pred in predicates:
        assert pred(dict(zip(lines, range(len(lines)))))
