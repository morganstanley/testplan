import sys
from functools import partial

import pytest

skip_on_windows = partial(pytest.mark.skipif, sys.platform == "win32")

is_311: bool = sys.version_info[0:2] >= (3, 11)


def _skip_module_on(reason: str, predicate: bool):
    if predicate:
        pytest.skip(reason, allow_module_level=True)


skip_module_on_windows = partial(
    _skip_module_on, predicate=sys.platform == "win32"
)

skip_module_on_311 = partial(_skip_module_on, predicate=is_311)
