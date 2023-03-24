import warnings
from typing import Any

import dill

FIFTY_MEGA = 52428800


class SerializationError(Exception):
    """general serialization error"""


class DeserializationError(Exception):
    """general deserialization error"""


def serialize(obj: Any) -> bytes:
    try:
        data = dill.dumps(obj)
        if len(data) > FIFTY_MEGA:
            warnings.warn(f"Too big object {obj} after serialization.")
        return data
    except TypeError:
        raise SerializationError(f"Type {type(obj)} cannot be serialized.")
    except dill.PickleError as exc:
        raise SerializationError(f"Failed to serialize {obj}") from exc


def deserialize(data: bytes) -> Any:
    try:
        return dill.loads(data)
    except EOFError:
        raise DeserializationError("No data input for deserialization.")
    except TypeError:
        raise DeserializationError(
            f"Type {type(data)} cannot be deserialized, bytes expected."
        )
    except dill.PickleError as exc:
        raise DeserializationError(f"Failed to deserialize.") from exc
