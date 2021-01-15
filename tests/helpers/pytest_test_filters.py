import sys
from functools import partial

import pytest

skip_on_windows = partial(pytest.mark.skipif, sys.platform == 'win32')
