from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import TextIOWrapper
from os import PathLike, SEEK_END
from typing import Union, Optional, Generic, TypeVar


class LogPosition:
    pass


T = TypeVar("T", str, bytes)


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

    def __init__(self, path: Union[PathLike, str], binary: bool) -> None:
        self._path = path
        self._binary = binary
        self._file: Optional[TextIOWrapper] = None

    @property
    def file(self):
        mode = "rb" if self._binary else "rt"
        if self._file is None:
            self._file = open(self._path, mode)
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
    def __init__(self, path: Union[PathLike, str]) -> None:
        super().__init__(path, True)


class TextFileLogStream(FileLogStream[str]):
    def __init__(self, path: Union[PathLike, str]) -> None:
        super().__init__(path, False)
