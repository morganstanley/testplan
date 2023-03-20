import warnings
from typing import Any

import dill

FIFTY_MEGA = 52428800


class TestplanSerializationError(Exception):
    """general serialization error"""


class TestplanDeserializationError(Exception):
    """general deserialization error"""


def serialize(obj: Any) -> bytes:
    try:
        data = dill.dumps(obj, byref=True)
        if len(data) > FIFTY_MEGA:
            warnings.warn(f"Too big object {obj} after serialization.")
        return data
    except (TypeError, dill.PickleError) as exc:
        raise TestplanSerializationError(str(obj)) from exc


def deserialize(data: bytes) -> Any:
    try:
        return dill.loads(data)
    except EOFError:
        raise TestplanDeserializationError(
            "No data input for deserialization."
        )
    except (TypeError, dill.PickleError) as exc:
        raise TestplanDeserializationError() from exc
