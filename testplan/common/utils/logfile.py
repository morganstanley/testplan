import fnmatch
import os
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from glob import glob
from io import TextIOWrapper
from itertools import dropwhile
from os import SEEK_END, PathLike
from typing import IO, Generic, List, Optional, TypeVar, Union
from testplan.common.remote.ssh_client import SSHClient


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

    def __del__(self) -> None:
        self.close()

    def reached_position(self, position: LogPosition) -> bool:
        return self.compare(self.position, position) >= 0


@dataclass
class LogfileInfo:
    inode: int
    path: str
    m_time: float


class LogRotationStrategy(ABC):
    @abstractmethod
    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        pass


class MTimeBasedLogRotationStrategy(LogRotationStrategy):
    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        path_string = os.fspath(path_info)
        files = [
            LogfileInfo(
                inode=os.stat(path).st_ino,
                path=path,
                m_time=os.stat(path).st_mtime_ns,
            )
            for path in reversed(glob(path_string))
        ]

        return list(sorted(files, key=lambda file_info: file_info.m_time))


class RotatedFileLogStream(LogStream[T]):
    @dataclass
    class FileLogPosition(LogPosition):
        inode: int
        position: int

        def __str__(self) -> str:
            return f"<position {self.position}>"

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
        self._file: Optional[IO[T]] = None

    @property
    def file(self) -> IO[T]:
        if self._file is None:
            self._open_first_file()

        return self._file  # type: ignore[return-value]

    def seek(self, position: Optional[LogPosition] = None) -> None:
        if position is None:
            self._open_first_file()
            return

        if not isinstance(position, self.FileLogPosition):
            raise TypeError(
                f"Expected self.FileLogPosition, got {type(position)!r}"
            )
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
        return self._empty_string().join(chunks)  # type: ignore[arg-type, return-value]

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

    def compare(  # type: ignore[override]
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
    def inode(self) -> int:
        return os.fstat(self.file.fileno()).st_ino

    @staticmethod
    @abstractmethod
    def _file_open_mode() -> str:
        pass

    def _open_file(self, path: str) -> None:
        self.close()
        self._file = open(path, self._file_open_mode())

    def _open_first_file(self) -> None:
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

    def _get_files(self) -> List[LogfileInfo]:
        return self._log_rotation_strategy.get_files(self._path_pattern)

    def _readall(self) -> T:
        chunks = [self.file.read(-1)]
        while self._open_next_file():
            chunks.append(self.file.read(-1))
        return self._empty_string().join(chunks)  # type: ignore[arg-type, return-value]

    @staticmethod
    @abstractmethod
    def _empty_string() -> Union[str, bytes]:
        pass


class BinaryFileOpenMode:
    @staticmethod
    def _file_open_mode() -> str:
        return "rb"

    @staticmethod
    def _empty_string() -> bytes:
        return b""


class TextFileOpenMode:
    @staticmethod
    def _file_open_mode() -> str:
        return "rt"

    @staticmethod
    def _empty_string() -> str:
        return ""


def get_remote_file_inode(
    ssh_client: SSHClient, path: Union[PathLike, str]
) -> int:
    path_string = os.fspath(path)
    _, inode_string, _ = ssh_client.exec_command(
        f"/usr/bin/stat -c %i '{path_string}'"
    )
    if not inode_string:
        raise RuntimeError(
            f"Cannot get stat for file {path} on {ssh_client.host}:{ssh_client.port}"
        )
    return int(inode_string)


class RemoteMTimeBasedLogRotationStrategy(MTimeBasedLogRotationStrategy):
    def __init__(
        self,
        ssh_client: SSHClient,
    ):
        super().__init__()
        self._ssh_client = ssh_client

    def get_files(self, path_info: Union[PathLike, str]) -> List[LogfileInfo]:
        path = pathlib.Path(path_info)
        files = []

        for file in self._ssh_client.listdir_iter(os.fspath(path.parent)):
            # Due to the sftp client limitation. we can not use glob directly.
            # Therefore, wildcards in the middle of the path are not supported.
            if fnmatch.fnmatch(file.filename, path.name):
                inode = get_remote_file_inode(
                    self._ssh_client, path.parent / file.filename
                )
                files.append(
                    LogfileInfo(
                        inode=inode,
                        path=os.fspath(path.parent / file.filename),
                        m_time=file.st_mtime,
                    )
                )

        return list(sorted(files, key=lambda file_info: file_info.m_time))


class RemoteRotatedFileLogStream(RotatedFileLogStream[T]):
    def __init__(
        self,
        ssh_client: SSHClient,
        path_pattern: Union[PathLike, str],
        rotation_strategy: LogRotationStrategy,
        binary: bool = False,
    ):
        self._ssh_client = ssh_client
        self._file_ino = 0
        super().__init__(path_pattern, rotation_strategy, binary)

    def _open_file(self, path: str) -> None:
        self.close()
        try:
            self._file = self._ssh_client.open_file(  # type: ignore[assignment]
                path, self._file_open_mode()
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Unable to open remote file {path}")
        self._file_ino = get_remote_file_inode(self._ssh_client, path)

    @property
    def position(self) -> RotatedFileLogStream.FileLogPosition:
        return self.FileLogPosition(self._file_ino, self.file.tell())

    @property
    def inode(self) -> int:
        return self._file_ino


class RotatedBinaryFileLogStream(
    BinaryFileOpenMode, RotatedFileLogStream[bytes]
):
    pass


class RotatedTextFileLogStream(TextFileOpenMode, RotatedFileLogStream[str]):
    pass


class RemoteRotatedBinaryFileLogStream(
    BinaryFileOpenMode, RemoteRotatedFileLogStream[bytes]
):
    pass


class RemoteRotatedTextFileLogStream(
    TextFileOpenMode, RemoteRotatedFileLogStream[str]
):
    pass
