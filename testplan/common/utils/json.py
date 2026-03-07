from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import orjson


def json_loads(data: str) -> Any:
    return orjson.loads(data)


def json_dumps(
    data: Any,
    indent_2: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
) -> str:
    return orjson.dumps(
        data,
        default=default,
        option=(orjson.OPT_INDENT_2 if indent_2 else 0)
        | orjson.OPT_SERIALIZE_NUMPY
        | orjson.OPT_NON_STR_KEYS,
    ).decode()


def json_load_from_path(path: Union[str, Path]) -> Dict[str, Any]:
    with open(path) as fp:
        result: Dict[str, Any] = json_loads(fp.read())
        return result
