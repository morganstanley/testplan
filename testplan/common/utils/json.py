import json
from pathlib import Path
from typing import Union

_USE_ORJSON = False

try:
    import orjson
except ImportError:
    pass
else:
    _USE_ORJSON = True


def json_loads(data: str):
    if _USE_ORJSON:
        return orjson.loads(data)
    else:
        return json.loads(data)


def json_dumps(data, indent_2=False, default=None) -> str:
    if _USE_ORJSON:
        return orjson.dumps(
            data,
            default=default,
            option=(orjson.OPT_INDENT_2 if indent_2 else 0)
            | orjson.OPT_SERIALIZE_NUMPY,
        ).decode()
    else:
        if default:

            class _E(json.JSONEncoder):
                def default(self, o):
                    return default(o)

        else:
            _E = None
        return json.dumps(data, cls=_E, indent=2 if indent_2 else None)


def json_load_from_path(path: Union[str, Path]) -> dict:
    with open(path) as fp:
        return json_loads(fp.read())
