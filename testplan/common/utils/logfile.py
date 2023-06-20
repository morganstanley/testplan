import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from glob import glob
from io import TextIOWrapper
from itertools import dropwhile
from os import PathLike, SEEK_END
from typing import Union, Optional, Generic, List, AnyStr


class LogPosition:
    pass


T = AnyStr


class LogStream(ABC, Generic[T]):
    @abstractmethod
    def seek(self, position: Optional[LogPosition] = None) -> None:
        pass

    @abstractmethod
    def read(self, size: int = -1) -> T:
        pass

    @abstractmethod
    def readline(self, size: int = -1) -> T:
        pass

    @property
    @abstractmethod
    def position(self) -> LogPosition:
        pass

    @abstractmethod
    def compare(self, position1: LogPosition, position2: LogPosition) -> int:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def flush(self) -> LogPosition:
        pass

    def __del__(self):
        self.close()

    def reached_position(self, position):
        return self.compare(self.position, position) >= 0


class FileLogStream(LogStream[T]):
    @dataclass
    class FileLogPosition(LogPosition):
        position: int = 0

    def __init__(self, path: Union[PathLike, str]) -> None:
        self._path = path
        self._file: Optional[TextIOWrapper] = None

    @staticmethod
    @abstractmethod
    def _file_open_mode() -> str:
        pass

    @property
    def file(self):
        if self._file is None:
            self._file = open(self._path, self._file_open_mode())
        return self._file

    def seek(self, position: Optional[FileLogPosition] = None) -> None:
        pos = 0 if not position else position.position
        self.file.seek(pos)

    def read(self, size: int = -1) -> T:
        return self.file.read(size)

    def readline(self, size=-1) -> T:
        return self.file.readline()

    @property
    def position(self) -> FileLogPosition:
        return self.FileLogPosition(position=self.file.tell())

    def compare(
        self, position1: FileLogPosition, position2: FileLogPosition
    ) -> int:
        return position1.position - position2.position

    def close(self) -> None:
        if self._file is not None:
            try:
                self._file.close()
            finally:
                self._file = None

    def flush(self) -> FileLogPosition:
        self._file.seek(0, SEEK_END)
        return self.position


class BinaryFileLogStream(FileLogStream[bytes]):
    @staticmethod
    def _file_open_mode():
        return "rb"


class TextFileLogStream(FileLogStream[str]):
    @staticmethod
    def _file_open_mode():
        return "rt"


@dataclass
class LogfileInfo:
    inode: int
    path: str


class LogRotationStrategy(ABC):
    @abstractmethod
    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        pass


class MTimeBasedLogRotationStrategy(LogRotationStrategy):
    @dataclass
    class MTimeLogfileInfo(LogfileInfo):
        m_time: float = field(init=False)

        def __post_init__(self):
            stat = os.stat(self.path)
            self.m_time = stat.st_mtime_ns

    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        path_string = os.fspath(path_info)
        files = [
            self.MTimeLogfileInfo(os.stat(path).st_ino, path)
            for path in reversed(glob(path_string))
        ]

        return list(sorted(files, key=lambda file_info: file_info.m_time))


class RotatedFileLogStream(LogStream[T]):
    @dataclass
    class FileLogPosition(LogPosition):
        inode: int
        position: int

    def __init__(
        self,
        path_pattern: Union[PathLike, str],
        rotation_strategy: LogRotationStrategy,
        binary: bool = False,
    ) -> None:
        self._path_pattern = path_pattern
        self._log_rotation_strategy = rotation_strategy
        self._binary = binary
        self._files: List[LogfileInfo]
        self._file = None

    @property
    def file(self) -> TextIOWrapper:
        if self._file is None:
            self._open_first_file()

        return self._file

    def seek(self, position: Optional[FileLogPosition] = None) -> None:
        if position is None:
            self._open_first_file()
            return

        if self._file is None or self.inode != position.inode:
            files = self._get_files()
            for file in files:
                if file.inode == position.inode:
                    self._open_file(file.path)
                    break
            else:
                raise FileNotFoundError(f"No logfile were found for")
        self.file.seek(position.position)

    def read(self, size: int = -1) -> T:
        if size == -1:
            return self._readall()

        remaining = size
        chunks = []
        while remaining > 0:
            chunk = self.file.read(remaining)
            remaining -= len(chunk)
            chunks.append(chunk)
            if remaining:
                if not self._open_next_file():
                    break
        return self._empty_string().join(chunks)

    def readline(self, size: int = -1) -> T:
        line = self.file.readline()
        while len(line) == 0 and self._open_next_file():
            line = self.file.readline()
        return line

    @property
    def position(self) -> FileLogPosition:
        return self.FileLogPosition(
            os.fstat(self.file.fileno()).st_ino, self.file.tell()
        )

    def flush(self) -> LogPosition:
        files = self._get_files()
        if files:
            self._open_file(files[-1].path)
            self.file.seek(0, SEEK_END)

        return self.position

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None

    def compare(
        self, position1: FileLogPosition, position2: FileLogPosition
    ) -> int:
        if position1.inode == position2.inode:
            return position1.position - position2.position

        inodes = [
            file.inode
            for file in self._get_files()
            if file.inode == position1.inode or file.inode == position2.inode
        ]

        if len(inodes) != 2:
            raise FileNotFoundError(
                "At least one of the positions is not valid"
            )

        if inodes[0] == position1.inode:
            # first in front
            return -1
        else:
            return 1

    @property
    def inode(self):
        return os.fstat(self.file.fileno()).st_ino

    @staticmethod
    @abstractmethod
    def _file_open_mode():
        pass

    def _open_file(self, path):
        self.close()
        self._file = open(path, self._file_open_mode())

    def _open_first_file(self):
        files = self._get_files()
        if files:
            self._open_file(files[0].path)
        else:
            raise FileNotFoundError(
                f"No logfile were found for: {self._path_pattern}"
            )

    def _open_next_file(self) -> bool:
        files = self._get_files()
        files = list(dropwhile(lambda file: file.inode != self.inode, files))

        if not files:
            raise FileNotFoundError("Current file is not on the list")
        if len(files) < 2:
            return False

        self._open_file(files[1].path)
        return True

    def _get_files(self):
        return self._log_rotation_strategy.get_files(self._path_pattern)

    def _readall(self):
        chunks = [self.file.read(-1)]
        while self._open_next_file():
            chunks.append(self.file.read(-1))
        return self._empty_string().join(chunks)

    @staticmethod
    @abstractmethod
    def _empty_string():
        pass


class RotatedBinaryFileLogStream(RotatedFileLogStream[bytes]):
    @staticmethod
    def _file_open_mode():
        return "rb"

    @staticmethod
    def _empty_string():
        return b""


class RotatedTextFileLogStream(RotatedFileLogStream[str]):
    @staticmethod
    def _file_open_mode():
        return "rt"

    @staticmethod
    def _empty_string():
        return ""
