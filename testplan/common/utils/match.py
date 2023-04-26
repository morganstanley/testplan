"""
Module of utility types and functions that perform matching.
"""
import os
import re
import time
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Match, Optional, Pattern, Tuple, TextIO, Union

from . import logger, timing

LOG_MATCHER_INTERVAL = 0.25


def match_regexps_in_file(
    logpath: os.PathLike, log_extracts: List[Pattern]
) -> Tuple[bool, Dict[str, str], List[Pattern]]:
    """
    Return a boolean, dict pair indicating whether all log extracts matches,
    as well as any named groups they might have matched.

    :param logpath: Log file path.
    :param log_extracts:  Regex list.
    :return: Match result.
    """
    extracted_values = {}

    if not os.path.exists(logpath):
        return False, extracted_values, log_extracts

    extracts_status = [False for _ in log_extracts]

    # If log_extracts contain bytes regex, will convert all log_extracts to
    # bytes regex.
    if not all([isinstance(x.pattern, str) for x in log_extracts]):
        read_mode = "rb"
        _log_extracts = []
        for regex in log_extracts:
            if not isinstance(regex.pattern, bytes):
                _log_extracts.append(re.compile(regex.pattern.encode("utf-8")))
            else:
                _log_extracts.append(regex)
    else:
        read_mode = "r"
        _log_extracts = log_extracts

    with open(logpath, read_mode) as log:
        for line in log:
            for pos, regexp in enumerate(_log_extracts):
                match = regexp.match(line)
                if match:
                    extracted_values.update(match.groupdict())
                    extracts_status[pos] = True

    unmatched = [
        exc for idx, exc in enumerate(log_extracts) if not extracts_status[idx]
    ]
    return all(extracts_status), extracted_values, unmatched


class LogFilePosition:
    """
    Class for managing the log file positions.
    """

    def __init__(self, inode: int, position: int):
        """
        :param inode: File inode of a log file.
        :type inode: ``int``
        :param position: Current position of a log file.
        :type position: ``int``
        """
        self.inode: int = inode
        self.position: int = position


class RotationStrategy(object, metaclass=ABCMeta):
    """
    Base rotation strategy with abstract methods to manage regex
    matching in log files. Implement all abstract methods if you
    need to subclass this class.
    """

    @abstractmethod
    def init_strategy(self, log_path: str) -> LogFilePosition:
        """
        Returns the initial log file position for the log_path.
        """
        raise NotImplementedError

    @abstractmethod
    def open_logfile_in_position(
        self, position: LogFilePosition, mode: str
    ) -> TextIO:
        """
        Implementation for opening and returning log handles with the
        given file position.
        """
        raise NotImplementedError

    @abstractmethod
    def get_position(self, file_handle: TextIO) -> LogFilePosition:
        """Returns the position for the given file handle."""
        raise NotImplementedError

    @abstractmethod
    def get_next_file(
        self, file_handle: TextIO, mode: Optional[str] = None
    ) -> Tuple[TextIO, bool]:
        """Returns the next file handle and a truthy value whether a new file was returned."""
        raise NotImplementedError

    @abstractmethod
    def get_end_of_file_position(self) -> LogFilePosition:
        """Returns the end position for the active log file."""
        raise NotImplementedError

    @abstractmethod
    def get_start_of_file_position(self) -> LogFilePosition:
        """Returns the start position for the first rotated log file if
        rotation occured else return start position of the active log file.
        """
        raise NotImplementedError

    @abstractmethod
    def invalid_position_order(
        self, start_position: LogFilePosition, end_position: LogFilePosition
    ) -> bool:
        """
        Checks the position validity of start_position and end_position.
        Return False if search starts from start_position through to end_position else
        return True.
        """
        raise NotImplementedError

    @abstractmethod
    def position_not_passed(
        self, position: LogFilePosition, file_handle: TextIO
    ) -> bool:
        """
        Checks if file_handle current position has not passed the parameter
        position value.
        """
        raise NotImplementedError


class NoLogRotationStrategy(RotationStrategy):
    """
    Default strategy for matching lines in log files. This strategy is used for situations with no log file rotation.
    """

    def __init__(self):
        self.log_path: Optional[str] = None
        self.inode: Optional[int] = None

    def init_strategy(self, log_path: str) -> LogFilePosition:
        """
        Returns the initial log file position for the log_path.
        """
        file_descriptor = None
        try:
            if os.path.exists(log_path):
                file_descriptor = os.open(log_path, os.O_RDONLY)
            else:
                file_descriptor = os.open(log_path, os.O_CREAT)

            self.inode = os.fstat(file_descriptor).st_ino
            self.log_path = log_path
            return LogFilePosition(inode=self.inode, position=0)
        finally:
            if file_descriptor:
                os.close(file_descriptor)

    def open_logfile_in_position(
        self, position: LogFilePosition, mode: str
    ) -> TextIO:
        """
        Opens and returns a file handle for the file position passed. Sets the position to the specified position.
        """
        log_handle = None
        try:
            log_handle = open(self.log_path, mode)
            log_handle.seek(position.position)
            return log_handle
        except IOError:
            if log_handle:
                log_handle.close()
            raise

    def get_position(self, file_handle: TextIO) -> LogFilePosition:
        """Returns the current position for the given file handle."""
        return LogFilePosition(inode=self.inode, position=file_handle.tell())

    def get_next_file(
        self, file_handle: TextIO, mode: Optional[str] = None
    ) -> Tuple[TextIO, bool]:
        """
        Returns a file handle with same position as file_handle and False value since it has no rotation.
        """
        log_handle = None
        try:
            log_handle = open(self.log_path, mode)
            log_handle.seek(file_handle.tell())
            return log_handle, False
        except IOError:
            if log_handle:
                log_handle.close()
            raise

    def get_end_of_file_position(self) -> LogFilePosition:
        """Returns the end position for the log file."""
        with open(self.log_path) as log_handle:
            log_handle.seek(0, os.SEEK_END)

            return LogFilePosition(
                inode=self.inode, position=log_handle.tell()
            )

    def get_start_of_file_position(self) -> LogFilePosition:
        """Returns the start position for the log file."""
        return LogFilePosition(inode=self.inode, position=0)

    def invalid_position_order(
        self, start_position: LogFilePosition, end_position: LogFilePosition
    ) -> bool:
        """
        Checks the position validity of start_position and end_position.
        Returns True if start_position has greater or equal position value than end_position,
        meaning search cannot be done from top of file to bottom of file. Else returns
        False.
        """
        return start_position.position >= end_position.position

    def position_not_passed(
        self, position: LogFilePosition, file_handle: TextIO
    ) -> bool:
        """
        Checks if file_handle current position has not passed the parameter
        position value. Return True if parameter position value is greater
        than current position of file_handle, meaning the search needs to continue
        else return False.
        """
        return position.position > file_handle.tell()


class LogMatcher(logger.Loggable):
    """
    Single line matcher for text files (usually log files). Once matched, it
    remembers the line number of the match and subsequent matches are scanned
    from the current line number. This can be useful when matched lines are not
    unique for the entire log file.
    """

    def __init__(
        self,
        log_path: str,
        strategy: RotationStrategy = NoLogRotationStrategy(),
    ):
        """
        :param log_path: Path to the log file.
        :type log_path: ``str``
        :param strategy: Strategy for matching rotated files.
        :type strategy: ``RotationStrategy``
        """
        self.log_path: str = log_path
        self.marks: Dict[str, LogFilePosition] = {}
        self.strategy: RotationStrategy = strategy
        self.position: LogFilePosition = self.strategy.init_strategy(
            log_path=log_path
        )
        super(LogMatcher, self).__init__()

    def seek(self, mark: Optional[str] = None):
        """
        Sets current file position to the specified mark. The mark has to exist.
        If the mark is None sets current file position to beginning of file.

        :param mark: Name of the mark.
        """
        if mark is None:
            self.position = self.strategy.get_start_of_file_position()
        else:
            self.position = self.marks[mark]

    def seek_eof(self):
        """Sets current file position to the current end of file."""
        self.position = self.strategy.get_end_of_file_position()

    def seek_sof(self):
        """Sets current file position to the start of file."""
        self.seek()

    def mark(self, name: str):
        """
        Marks the current file position with the specified name. The mark name
        can later be used to set the file position

        :param name: Name of the mark.
        """
        self.marks[name] = self.position

    def match(
        self,
        regex: Union[str, bytes, Pattern],
        timeout: float = 5,
        raise_on_timeout: bool = True,
    ) -> Optional[Match]:
        """
        Matches each line in the log file from the current line number to the
        end of the file. If a match is found the line number is stored and the
        match is returned. Can be configured to raise an exception if no match
        is found.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :param timeout: Timeout in seconds to wait for matching process,
            0 means matching till EOF and not waiting for new lines, any
            value greater than 0 means doing matching up to such seconds,
            defaults to 5 seconds
        :param raise_on_timeout: To raise TimeoutException or not
        :return: The regex match or None if no match is found
        """
        match = None
        start_time = time.time()
        end_time = start_time + timeout
        read_mode = "rb"
        log_handle = None

        # As a convenience, we create the compiled regex if a string was
        # passed.
        if not hasattr(regex, "match"):
            regex = re.compile(regex)
        if isinstance(regex.pattern, str):
            read_mode = "r"

        try:
            log_handle = self.strategy.open_logfile_in_position(
                position=self.position, mode=read_mode
            )

            while True:
                if (timeout > 0) and (time.time() > end_time):
                    break

                line = log_handle.readline()
                if line:
                    match = regex.match(line)
                    if match:
                        break
                else:

                    previous_log_handle = log_handle

                    log_handle, is_new_file = self.strategy.get_next_file(
                        file_handle=log_handle, mode=read_mode
                    )

                    previous_log_handle.close()

                    # If new file continue search, else check if timeout is
                    # greater than zero and wait awhile else break the search.
                    if is_new_file:
                        continue
                    elif timeout > 0:
                        time.sleep(LOG_MATCHER_INTERVAL)
                    else:
                        break

            self.position = self.strategy.get_position(file_handle=log_handle)
        finally:
            if log_handle:
                log_handle.close()

        if match is not None:
            self.logger.debug(
                "Match[%s] found in %.2fs",
                regex.pattern,
                time.time() - start_time,
            )
        elif timeout and raise_on_timeout:
            raise timing.TimeoutException(
                "No match[{}] found in {}s".format(regex.pattern, timeout)
            )

        return match

    def not_match(self, regex: Union[str, bytes, Pattern], timeout: float = 5):
        """
        Opposite of :py:meth:`~testplan.common.utils.match.LogMatcher.match`
        which raises an exception if a match is found. Matching is performed
        from the current file position. If match is not found within timeout
        period then no exception is raised.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :param timeout: Timeout in seconds to wait for matching process,
            0 means should not wait and return whatever matched on initial
            scan, defaults to 5 seconds
        """

        match = self.match(regex, timeout, raise_on_timeout=False)
        if match is not None:
            raise Exception(
                f"Unexpected match[{regex.pattern}] found in {timeout}s"
            )

    def match_all(
        self,
        regex: Union[str, bytes, Pattern],
        timeout: float = 5,
        raise_on_timeout: bool = True,
    ) -> List[Match]:
        """
        Similar to match, but returns all occurrences of regex. Can be
        configured to raise an exception if no match is found.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :param timeout: Timeout in seconds to find out all matches in file,
            defaults to 5 seconds.
        :param raise_on_timeout: To raise TimeoutException or not
        :return: A list of regex matches
        """
        matches = []
        end_time = time.time() + timeout

        try:
            while timeout >= 0:
                matches.append(
                    self.match(regex, timeout, raise_on_timeout=True)
                )
                timeout = end_time - time.time()
        except timing.TimeoutException:
            if not matches and raise_on_timeout:
                raise

        return matches

    def match_between(self, regex, mark1, mark2):
        """
        Matches file against passed in regex. Matching is performed from
        file position denoted by mark1 and ends before file position denoted
        by mark2. If a match is not found then None is returned.

        :param regex: regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern, bytes]``
        :param mark1: mark name of start position (None for beginning of file)
        :type mark1: ``str``
        :param mark2: mark name of end position
        :type mark2: ``str``
        """
        match = None
        read_mode = "rb"
        log_handle = None

        # As a convenience, we create the compiled regex if a string was
        # passed.
        if not hasattr(regex, "match"):
            regex = re.compile(regex)
        if isinstance(regex.pattern, str):
            read_mode = "r"

        try:
            start_position = self.marks[mark1]
            end_position = self.marks[mark2]

            if self.strategy.invalid_position_order(
                start_position=start_position, end_position=end_position
            ):
                raise ValueError(
                    f'Mark "{mark2}" must be present before mark "{mark1}"'
                )

            log_handle = self.strategy.open_logfile_in_position(
                position=start_position, mode=read_mode
            )

            while self.strategy.position_not_passed(
                position=end_position, file_handle=log_handle
            ):
                line = log_handle.readline()

                if line:
                    match = regex.match(line)
                    if match:
                        break
                else:
                    previous_log_handle = log_handle

                    log_handle, _ = self.strategy.get_next_file(
                        file_handle=log_handle, mode=read_mode
                    )

                    previous_log_handle.close()

            return match
        except KeyError:
            raise ValueError(f'Mark "{mark1}" or "{mark2}" does not exist')
        finally:
            if log_handle:
                log_handle.close()

    def not_match_between(self, regex, mark1, mark2):
        """
        Opposite of :py:meth:`~testplan.common.utils.match.LogMatcher.match_between`
        which returns None if a match is not found. Matching is performed
        from file position denoted by mark1 and ends before file position
        denoted by mark2. If a match is found then False is returned otherwise True.

        :param regex: regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern, bytes]``
        :param mark1: mark name of start position (None for beginning of file)
        :type mark1: ``str``
        :param mark2: mark name of end position
        :type mark2: ``str``
        """

        return not self.match_between(regex, mark1, mark2)

    def get_between(self, mark1=None, mark2=None):
        """
        Returns the content of the file from the start marker to the end marker.
        It is possible to omit either marker to receive everything from start
        to end of file.

        .. note::

            Since markers point to the byte position immediately after match,
            this function will not return what was matched for mark1, but will
            return the contents of what was matched for mark2.

        :param mark1: mark name of start position (None for beginning of file)
        :type mark1: ``str``
        :param mark2: mark name of end position (None for end of file)
        :type mark2: ``str``
        :return: The content between mark1 and mark2.
        :rtype: ``str``
        """
        try:
            log_handle = None

            if mark1 is not None and mark2 is not None:
                if self.strategy.invalid_position_order(
                    start_position=self.marks[mark1],
                    end_position=self.marks[mark2],
                ):
                    raise ValueError(
                        f'Mark "{mark2}" must be present before mark "{mark1}"'
                    )

            lines_between = []
            start_position = (
                self.marks[mark1]
                if mark1 is not None
                else self.strategy.get_start_of_file_position()
            )

            end_position = (
                self.marks[mark2]
                if mark2 is not None
                else self.strategy.get_end_of_file_position()
            )

            log_handle = self.strategy.open_logfile_in_position(
                position=start_position, mode="r"
            )

            while self.strategy.position_not_passed(
                position=end_position, file_handle=log_handle
            ):
                line = log_handle.readline()

                if line:
                    lines_between.append(line)
                else:
                    previous_log_handle = log_handle

                    log_handle, _ = self.strategy.get_next_file(
                        file_handle=log_handle, mode="r"
                    )

                    previous_log_handle.close()

            return "".join(lines_between)
        except KeyError:
            raise ValueError(f'Mark "{mark1}" or "{mark2}" does not exist')
        finally:
            if log_handle:
                log_handle.close()
