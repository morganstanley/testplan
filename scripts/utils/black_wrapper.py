#!/usr/bin/env python
"""
Wrapper utility for the black code-formatter.

Handles:
    - Sets line length to 79 chars
    - Excludes vendored dependencies and any python files under node_modules
    - Includes --check option for CI. Do nothing if called in check mode with
      a python 2 interpreter.
"""
import argparse
import os
import subprocess
import sys

import six

THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir, os.pardir))


def main():
    args = make_parser().parse_args()

    if six.PY2:
        if args.check:
            # It is expected that Travis will call this script with Python 2
            # in CI - do nothing and return 0 so as not to fail the build.
            print("Skipping black check on python 2")
            return 0
        else:
            print("Black requires python 3")
            return -1

    cmd = [
        "black",
        "--check",
        "-l",
        "79",
        "--exclude",
        "vendor|node_modules",
        ROOT_DIR,
    ]

    return subprocess.run(cmd).returncode


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that files are formatted correctly, do not make any "
             "changes."
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
