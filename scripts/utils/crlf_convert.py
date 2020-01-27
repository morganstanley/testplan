#!/usr/bin/env python3
import os
import subprocess
import re
from typing import Generator

THIS_DIR = os.path.dirname(__file__)
CHECK_SCRIPT = os.path.join(THIS_DIR, "crlf_check.sh")
STDOUT_RX = re.compile(r"([^:]*):.*CRLF.*")


def main():
    result = subprocess.run([CHECK_SCRIPT], capture_output=True, text=True)
    if result.returncode == 0:
        # Nothing to do
        print("Nothing needs converting - great job")
        return

    for filename in filenames(result.stdout):
        subprocess.run(["dos2unix", filename], check=True)

    print("Convered all files to unix line endings.")


def filenames(stdout: str) -> Generator[str, None, None]:
    for line in stdout.splitlines():
        match = STDOUT_RX.match(line)
        if match:
            yield match.group(1)


if __name__ == "__main__":
    main()
