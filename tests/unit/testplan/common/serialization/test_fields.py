"""
Unit tests for the testplan.common.serialization.fields module.
"""
import pytest

from testplan.common.serialization import fields


@pytest.fixture
def native_or_pretty():
    return fields.NativeOrPretty()


class SerializeMe(object):
    """Custom type that returns a string as its "serialization"."""

    def __repr__(self):
        return "I have been serialized!"


class UnPickleableInt(int):
    """A type that derives from int but cannot itself be serialized."""

    def __getstate__(self):
        raise NotImplementedError

    def __repr__(self):
        return "{}[{}]".format(
            self.__class__.__name__, super(UnPickleableInt, self).__repr__()
        )


class SerializationTargets(object):
    """
    An object that contains some different values to be serialized for
    testing.
    """

    def __init__(self):
        self.x = 123
        self.y = "foo"
        self.z = None

        self.serializable = SerializeMe()
        self.unpickleable = UnPickleableInt(42)


@pytest.fixture
def targets():
    return SerializationTargets()


class TestNativeOrPretty(object):
    def test_basic(self, native_or_pretty, targets):
        """Test serialization of basic types: no change is required."""
        for attr in ("x", "y", "z"):
            serialized = native_or_pretty.serialize(attr, targets)
            assert serialized == getattr(targets, attr)

    def test_format(self, native_or_pretty, targets):
        """Test serializing of a custom type."""
        serialized = native_or_pretty.serialize("serializable", targets)
        assert serialized == "I have been serialized!"

    def test_derived_type(self, native_or_pretty, targets):
        """
        Test serializing of a type that inherits from a builtin, but is not
        itself pickle-able. The correct behaviour is to return a formatted
        string.
        """
        serialized = native_or_pretty.serialize("unpickleable", targets)
        assert serialized == "UnPickleableInt[42]"
