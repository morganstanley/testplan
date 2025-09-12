from pathlib import Path
from typing import Union

import orjson


def json_loads(data: str):
    return orjson.loads(data)


def json_dumps(data, indent_2=False, default=None) -> str:
    return orjson.dumps(
        data,
        default=default,
        option=(orjson.OPT_INDENT_2 if indent_2 else 0)
        | orjson.OPT_SERIALIZE_NUMPY
        | orjson.OPT_NON_STR_KEYS,
    ).decode()


def json_load_from_path(path: Union[str, Path]) -> dict:
    with open(path) as fp:
        return json_loads(fp.read())
