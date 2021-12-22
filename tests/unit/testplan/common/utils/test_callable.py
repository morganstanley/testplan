import operator

from testplan.common.utils.callable import dispatchmethod


class Data(object):
    def __init__(self, val):
        self.val = val


class DataProcessor(object):
    @dispatchmethod
    def enlarge(self, data):
        return Data(data.val.upper())

    @enlarge.register(str)
    def _(self, data):
        return " ".join([data] * 5)

    @enlarge.register(int)
    def _(self, data):
        return data ** 3

    @dispatchmethod(in_list=True)
    def sort_list(self, lst):
        return sorted(lst, key=operator.attrgetter("val"))

    @sort_list.register(str)
    def _(self, lst):
        return sorted(lst)

    @sort_list.register(int)
    def _(self, lst):
        return sorted(lst, reverse=True)


def test_dispatchmethod():
    """
    Test that `dispatchmethod` can be used as a decorator with or
    without argument `in_list` (default False) for instance methods.
    """
    processor = DataProcessor()
    assert processor.enlarge("hey") == "hey hey hey hey hey"
    assert processor.enlarge(10) == 1000
    assert processor.enlarge(Data("hello")).val == "HELLO"
    assert processor.sort_list(["hi", "foo", "bar"]) == ["bar", "foo", "hi"]
    assert processor.sort_list([5, 0, -1, 8, 2]) == [8, 5, 2, 0, -1]
    assert [
        data.val
        for data in processor.sort_list(
            [Data("uvw"), Data("abc"), Data("123"), Data("xyz"), Data("-=+")]
        )
    ] == ["-=+", "123", "abc", "uvw", "xyz"]
