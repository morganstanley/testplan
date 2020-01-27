#!/usr/bin/env python
"""Run the black check on python 3, do nothing on python 2."""
import subprocess
import sys

import six


def main():
    if six.PY2:
        print("Skipping black check on python 2")
        return 0

    cmd = [
        "python",
        "-m",
        "black",
        "--check",
        "-l",
        "79",
        "--exclude",
        "vendor|node_modules",
        ".",
    ]

    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
