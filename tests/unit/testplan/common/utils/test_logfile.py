import os.path
import time
from contextlib import closing
from dataclasses import dataclass
from glob import glob
from os import PathLike
from typing import Union, List, Optional

import pytest
from boltons.iterutils import chunked

from testplan.common.utils.logfile import (
    RotatedFileLogStream,
    LogfileInfo,
    LogRotationStrategy,
    MTimeBasedLogRotationStrategy,
)


class SimpleNameBasedStrategy(LogRotationStrategy):
    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        return [
            LogfileInfo(os.stat(path).st_ino, path)
            for path in reversed(sorted(glob(path_info)))
        ]


@dataclass
class RotationStrategyConfig:
    strategy: LogRotationStrategy
    wait: Optional[float] = None


@pytest.fixture(
    params=[
        RotationStrategyConfig(SimpleNameBasedStrategy()),
        RotationStrategyConfig(MTimeBasedLogRotationStrategy(), 0.01),
    ],
    ids=["SimpleNameBasedStrategy", "MTimeBasedLogRotationStrategy"],
)
def rotation_strategy(request) -> RotationStrategyConfig:
    return request.param


def populate_logfiles(rotating_logger, num_logs, lines, binary, wait=None):
    file_num = 0
    log_content = []

    while True:
        for i in range(lines):
            line = f"Test_log {file_num}.{i}"
            if binary:
                content = (line + os.linesep).encode()
            else:
                content = line + "\n"

            log_content.append(content)
            rotating_logger.info(line)
        file_num += 1
        if file_num < num_logs:
            if wait:
                time.sleep(wait)
            rotating_logger.doRollover()
        else:
            break

    return log_content


@pytest.fixture(params=[(1, 4), (3, 4)], ids=["single", "multiple"])
def prepare_logfiles(request):
    num_logs, lines = request.param

    def prepare_func(rotating_logger, binary, wait=None):
        return populate_logfiles(
            rotating_logger, num_logs, lines, binary, wait
        )

    return prepare_func


@pytest.fixture(params=[True, False])
def binary(request):
    return request.param


class TestRotatedFileLogStream:
    def test_readline(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):
        empty_line = b"" if binary else ""
        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )
        with closing(stream):
            for line in log_content:
                assert stream.readline() == line

            # check if we read after the end of files
            assert stream.readline() == empty_line
            assert stream.readline() == empty_line

    def test_readall(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):
        empty_line = b"" if binary else ""
        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )
        with closing(stream):
            assert stream.read() == empty_line.join(log_content)

        # another read goes from the start
        with closing(stream):
            assert stream.read() == empty_line.join(log_content)

    def test_read(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):
        empty_line = b"" if binary else ""
        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )
        log = empty_line.join(log_content)
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )
        read_size = len(log_content[0]) // 2 - 1
        with closing(stream):
            for chunk in chunked(log, read_size):
                assert stream.read(read_size) == chunk

        # reading reopen the stream from start
        with closing(stream):
            assert stream.read(10) == log[:10]

    def test_seek(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):
        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )

        @dataclass
        class PosContent:
            position: RotatedFileLogStream.FileLogPosition
            content: Union[str, bytes]

        positions = []
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )
        with closing(stream):
            for _ in range(len(log_content)):
                pos = stream.position
                line = stream.readline()
                positions.append(PosContent(pos, line))

            # go backward one by one seeking
            for pos in reversed(positions):
                stream.seek(pos.position)
                assert stream.position == pos.position
                assert stream.readline() == pos.content

    def test_flush(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):
        empty_line = b"" if binary else ""
        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )

        with closing(stream):

            assert stream.readline() == log_content[0]
            end = stream.flush()
            assert stream.readline() == empty_line
            assert stream.position == end

            line = "one more line"
            rotating_logger.info(line)

            if binary:
                expected = (line + os.linesep).encode()
            else:
                expected = line + "\n"

            assert stream.readline() == expected

    def test_compare(
        self, rotating_logger, binary, rotation_strategy, prepare_logfiles
    ):

        log_content = prepare_logfiles(
            rotating_logger, binary, rotation_strategy.wait
        )
        log_length = sum(map(len, log_content))
        stream = RotatedFileLogStream(
            rotating_logger.pattern, rotation_strategy.strategy, binary
        )

        with closing(stream):
            # same pos
            pos1 = stream.position
            assert stream.compare(pos1, pos1) == 0

            # same file
            stream.readline()
            pos2 = stream.position
            assert stream.compare(pos1, pos2) < 0
            assert stream.compare(pos2, pos1) > 0

            # different files
            stream.seek()
            stream.read(log_length // 4)
            pos1 = stream.position

            stream.read(log_length // 2)
            pos2 = stream.position

            assert stream.compare(pos1, pos2) < 0
            assert stream.compare(pos2, pos1) > 0
