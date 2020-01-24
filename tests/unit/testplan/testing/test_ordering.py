import pytest

from testplan.common.utils.testing import py_version_data
from testplan.testing import ordering


def test_noop_sorter():
    sorter = ordering.NoopSorter()

    arr = [1, 2, 3, 4]
    assert arr == sorter.sorted_instances(arr)
    assert arr == sorter.sorted_testsuites(arr)
    assert arr == sorter.sorted_testcases(arr)


@pytest.mark.parametrize(
    "value, expected",
    (
        ("all", "all"),
        ("instances", "instances"),
        ("suites", "suites"),
        ("testcases", "testcases"),
        (ordering.SortType.ALL, "all"),
        (ordering.SortType.INSTANCES, "instances"),
        (ordering.SortType.SUITES, "suites"),
        (ordering.SortType.TEST_CASES, "testcases"),
        (("instances", "suites"), ["instances", "suites"]),
        ((ordering.SortType.INSTANCES, "suites"), ["instances", "suites"]),
    ),
)
def test_shuffle_type_enum_validate(value, expected):
    assert ordering.SortType.validate(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        "foo",
        1,
        object(),
        [1, 2],
        ("all", "testcases"),
        ("testcases", "something-else"),
    ),
)
def test_shuffle_type_enum_validate_failure(value):
    with pytest.raises(ValueError):
        ordering.SortType.validate(value)


expected_shuffled = py_version_data(py2=[1, 2, 5, 3, 4], py3=[1, 2, 4, 3, 5])


class TestShuffleSorter(object):
    def test_shuffle(self):
        arr = [1, 2, 3, 4, 5, 6, 7, 8]
        shuffled = list(arr)

        sorter = ordering.ShuffleSorter(seed=5)
        sorter.randomizer.shuffle(shuffled)

        assert shuffled != arr
        assert sorter.sorted_instances(arr) == shuffled
        assert sorter.sorted_testsuites(arr) == shuffled
        assert sorter.sorted_testcases(arr) == shuffled

    @pytest.mark.parametrize(
        "shuffle_types, expected",
        (
            ("instances", expected_shuffled),
            (("testcases", "instances"), expected_shuffled),
            ("all", expected_shuffled),
            ("testcases", [1, 2, 3, 4, 5]),
            ("suites", [1, 2, 3, 4, 5]),
        ),
    )
    def test_sorted_instances(self, shuffle_types, expected):
        sorter = ordering.ShuffleSorter(seed=5, shuffle_type=shuffle_types)
        arr = [1, 2, 3, 4, 5]
        assert expected == sorter.sorted_instances(arr)

    @pytest.mark.parametrize(
        "shuffle_types, expected",
        (
            ("suites", expected_shuffled),
            (("testcases", "suites"), expected_shuffled),
            ("all", expected_shuffled),
            ("testcases", [1, 2, 3, 4, 5]),
            ("instances", [1, 2, 3, 4, 5]),
        ),
    )
    def test_sorted_testsuites(self, shuffle_types, expected):
        sorter = ordering.ShuffleSorter(seed=5, shuffle_type=shuffle_types)
        arr = [1, 2, 3, 4, 5]
        assert expected == sorter.sorted_testsuites(arr)

    @pytest.mark.parametrize(
        "shuffle_types, expected",
        (
            ("testcases", expected_shuffled),
            (("testcases", "suites"), expected_shuffled),
            ("all", expected_shuffled),
            ("suites", [1, 2, 3, 4, 5]),
            ("instances", [1, 2, 3, 4, 5]),
        ),
    )
    def test_sorted_testcases(self, shuffle_types, expected):
        sorter = ordering.ShuffleSorter(seed=5, shuffle_type=shuffle_types)
        arr = [1, 2, 3, 4, 5]
        assert expected == sorter.sorted_testcases(arr)
