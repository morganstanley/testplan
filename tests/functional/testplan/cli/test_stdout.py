import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_PLAN = DATA_DIR / "sample_plan.py"

IGNORED_PATTERNS = [
    r"^Testplan\[.+\] has runpath: .+ and pid \d+$",
    r"^TestplanResult\[.+\]$",
]
IGNORED_PATTERNS = [re.compile(p) for p in IGNORED_PATTERNS]


@pytest.mark.parametrize("add_hooks", [False, True])
def test_sample_plan_stdout(add_hooks):
    """Run the sample plan as a CLI script and compare stdout to expected."""
    env = os.environ.copy()
    if add_hooks:
        env["ADD_HOOKS"] = "1"
    env["NO_COLOR"] = "1"  # disable colors in output

    cmd = [sys.executable, str(SAMPLE_PLAN)]
    proc = subprocess.run(
        cmd,
        env=env,
        text=True,
        check=False,
        capture_output=True,
    )

    # check if plan executed successfully
    assert proc.returncode == 0, (
        f"Exit {proc.returncode}\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
    )

    expected_stdout = (
        DATA_DIR / f"sample_plan_expected_stdout_{int(add_hooks)}.data"
    )
    # read expected lines
    with open(expected_stdout, "r", encoding="utf-8") as f:
        expected_lines = f.read().strip().splitlines()

    # filter actual lines
    actual_lines = []
    for line in proc.stdout.strip().splitlines():
        if not line:
            continue
        if any(p.match(line) for p in IGNORED_PATTERNS):
            continue
        actual_lines.append(line)

    # compare lengths first
    assert len(actual_lines) == len(expected_lines), (
        f"Expected {len(expected_lines)} lines after filtering, "
        f"got {len(actual_lines)} lines",
    )

    # compare stdout line by line
    assert all(exp == act for act, exp in zip(actual_lines, expected_lines)), (
        "Stdout mismatch",
    )
