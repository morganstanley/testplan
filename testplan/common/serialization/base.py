import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable

import dill

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

FIFTY_MEGA = 52428800


class SerializationError(Exception):
    """general serialization error"""


class DeserializationError(Exception):
    """general deserialization error"""


def serialize(obj: Any) -> bytes:
    try:
        data = dill.dumps(obj)
        if len(data) > FIFTY_MEGA:
            warnings.warn(
                f"Too big object {obj} of type {type(obj)} after serialization."
            )
        return data
    except TypeError as exc:
        raise SerializationError(
            f"{str(exc).capitalize()}, unexpected type within {obj} of type {type(obj)}."
        )
    except dill.PickleError as exc:
        raise SerializationError(
            f"Failed to serialize {obj} of type {type(obj)}."
        ) from exc


def deserialize(data: bytes) -> Any:
    try:
        return dill.loads(data)
    except EOFError:
        raise DeserializationError("No data input for deserialization.")
    except TypeError as exc:
        raise DeserializationError(f"{str(exc).capitalize()}.")
    except dill.PickleError as exc:
        raise DeserializationError(f"Failed to deserialize {data}.") from exc


class SelectiveSerializable(ABC):
    @property
    @abstractmethod
    def serializable_attrs(self) -> Iterable[str]:
        """Attributes to be included in serialization."""

    def dumps(self) -> bytes:
        """serialize"""
        data = {}
        for attr in self.serializable_attrs:
            data[attr] = getattr(self, attr)
        return serialize(data)

    def loads(self, obj: bytes) -> Self:
        """deserialize"""
        data: Dict[str, Any] = deserialize(obj)
        for attr, value in data.items():
            setattr(self, attr, value)
        return self
