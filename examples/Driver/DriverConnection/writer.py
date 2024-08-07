"""
Sample python script that writes to a file
"""

import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, format="%(message)s")


class Writer:
    def __init__(self):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self.file = os.path.join(os.getcwd(), "test.txt")

    def loop(self):
        with open(self.file, "w"):
            self._logger.info("Writing to file: %s", self.file)
            while True:
                continue


if __name__ == "__main__":
    writer = Writer()
    writer.loop()
