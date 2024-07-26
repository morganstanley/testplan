"""
Sample python script that reads from a file
"""

import sys
import logging

logging.basicConfig(stream=sys.stdout, format="%(message)s")


class Reader:
    def __init__(self, file):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self.file = file

    def loop(self):
        with open(self.file, "r"):
            self._logger.info("Reading from file: %s", self.file)
            while True:
                continue


if __name__ == "__main__":
    sys.stderr.flush()
    _, file_path = sys.argv
    reader = Reader(file_path)
    reader.loop()