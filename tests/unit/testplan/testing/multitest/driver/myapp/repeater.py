#!/usr/bin/env python
"""
Simple script that just mirrors stdin back to stdout, until either EOF signal
is received or the string literal "EOF" is input.
"""
import sys

SENTINEL = "EOF"


def main():
    for line in sys.stdin:
        if line.strip() == SENTINEL:
            break
        else:
            print(line.rstrip("\n"))


if __name__ == "__main__":
    main()
