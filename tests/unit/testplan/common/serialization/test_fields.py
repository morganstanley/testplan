"""
Unit tests for the testplan.common.serialization.fields module.
"""

import pytest
import re

from testplan.common.serialization import fields


@pytest.fixture
def native_or_pretty():
    return fields.NativeOrPretty()


class SerializeMe:
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


class SerializationTargets:
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


class TestNativeOrPretty:
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


class TestNormalizeForJson:
    """Tests for ``fields.normalize_for_json``."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (float("nan"), "NaN"),
            (float("inf"), "Infinity"),
            (float("-inf"), "-Infinity"),
            (1.5, 1.5),
        ],
    )
    def test_nan_and_infinity(self, value, expected):
        assert fields.normalize_for_json(value) == expected

    @pytest.mark.parametrize(
        "value, in_range",
        [
            (0, True),
            (1, True),
            (-(2**63) - 1, False),
            (2**64, False),
        ],
    )
    def test_int_orjson_range_boundary(self, value, in_range):
        result = fields.normalize_for_json(value)
        if in_range:
            assert result == value and isinstance(result, int)
        else:
            assert result == str(value)

    def test_bool_is_not_treated_as_int(self):
        # bool subclasses int, must skip int-range check.
        assert fields.normalize_for_json(True) is True
        assert fields.normalize_for_json(False) is False

    def test_non_json_safe_scalar_is_stringified(self):
        target = SerializeMe()
        assert fields.normalize_for_json(target) == "I have been serialized!"

    def test_nested_structure_is_fixed_in_place(self):
        value = {
            "a": [float("nan"), 2**64, "ok"],
            "b": {"c": float("inf"), "d": True},
        }
        result = fields.normalize_for_json(value)
        assert result == {
            "a": ["NaN", str(2**64), "ok"],
            "b": {"c": "Infinity", "d": True},
        }


class TestNativeOrPformat:
    """Tests for ``fields.native_or_pformat``."""

    def test_bytes_are_stringified(self):
        value = b"binary\xb1"
        assert fields.native_or_pformat(value) == str(value)

    @pytest.mark.parametrize(
        "value, expected",
        [
            (float("nan"), "NaN"),
            (float("inf"), "Infinity"),
            (float("-inf"), "-Infinity"),
            (1.5, 1.5),
        ],
    )
    def test_nan_and_infinity(self, value, expected):
        assert fields.native_or_pformat(value) == expected

    @pytest.mark.parametrize(
        "value, in_range",
        [
            (0, True),
            (1, True),
            (-(2**63) - 1, False),
            (2**64, False),
        ],
    )
    def test_int_orjson_range_boundary(self, value, in_range):
        result = fields.native_or_pformat(value)
        if in_range:
            assert result == value and isinstance(result, int)
        else:
            assert result == str(value)

    def test_bool_is_not_treated_as_int(self):
        assert fields.native_or_pformat(True) is True
        assert fields.native_or_pformat(False) is False


class TestNativeOrText:
    """Tests for ``fields.native_or_text``."""

    def test_preserves_primitives_and_formats_known_types(self):
        def my_order():
            pass

        assert fields.native_or_text(1000) == 1000
        assert fields.native_or_text(True) is True
        assert fields.native_or_text(None) is None
        assert fields.native_or_text(re.compile("a.*b")) == "REGEX(a.*b)"
        assert fields.native_or_text(my_order) == "my_order"

    def test_renders_complex_values_as_text(self):
        assert fields.native_or_text({"a": [1, 2]}) == "{'a': [1, 2]}"
        assert fields.native_or_text({"third", "first", "second"}) == (
            "['first', 'second', 'third']"
        )

    def test_handles_recursive_and_broken_values(self):
        class BrokenString:
            def __str__(self):
                raise RuntimeError("cannot render")

        recursive = []
        recursive.append(recursive)

        assert fields.native_or_text(recursive) == "[[...]]"
        assert fields.native_or_text(BrokenString()) == "<BrokenString>"

    def test_truncation_is_idempotent(self):
        result = fields.native_or_text("x" * 2000)

        assert result == "x" * 1000 + "..."
        assert fields.native_or_text(result) == result
