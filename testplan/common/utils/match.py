"""
Module of utility types and functions that perform matching.
"""
import os
import re
import time
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Match, Optional, Pattern, Tuple, Union

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

    def __init__(self, file_inode, marker):
        """
        :param file_inode: File inode of a log file.
        :type file_inode: ``int``
        :param marker: Current mark of a log file.
        :type marker: ``int``
        """
        self.file_inode = file_inode
        self.marker = marker

    def get_position(self, file_handle=None):
        """
        Return the instance file position given the specified file handle.
        """
        if file_handle:
            self.marker = file_handle.tell()
            file_handle.close()
        return self

    def seek_position(self, position):
        """
        Sets the file position to the position passed and return the instance
        file position.
        """
        self.file_inode = position.file_inode
        self.marker = position.marker
        return self


class RotationStrategy(object, metaclass=ABCMeta):
    """
    Base rotation strategy with abstract methods to manage regex
    matching in log files. Implement all abstract methods if you
    need to subclass this class.
    """

    @abstractmethod
    def open_logfile_in_position(self, file_position, mode) -> LogFilePosition:
        """
        Implementation for opening and returning log handles with the
        given file position.
        """
        raise NotImplementedError

    @abstractmethod
    def get_position(self, file_handle=None) -> LogFilePosition:
        """Return the current position for the given file handle."""
        raise NotImplementedError

    @abstractmethod
    def get_next_file(self, file_handle, mode=None, affect_position=True):
        """Returns the next file handle."""
        raise NotImplementedError

    @abstractmethod
    def get_inode_and_marker(self, file_handle) -> tuple:
        """Returns the inode and marker for the given file handle."""
        raise NotImplementedError

    @abstractmethod
    def seek_eof(self) -> LogFilePosition:
        """Returns the end file position of the current log file."""
        raise NotImplementedError

    @abstractmethod
    def seek(self, mark=None) -> LogFilePosition:
        """
        Set current file position to the specified mark if exist or beginning of current log file.
        """
        raise NotImplementedError

    @abstractmethod
    def get_end_of_file_position(self) -> LogFilePosition:
        """Returns the end position for the current log file."""
        raise NotImplementedError

    @abstractmethod
    def get_start_of_file_position(self) -> LogFilePosition:
        """Returns the start position for the current log file."""
        raise NotImplementedError


class NoLogRotationStrategy(RotationStrategy):
    """
    Default strategy for matching lines in log files. This strategy is used
    for situations with no log file rotation.
    """

    def __init__(self, log_path):
        """
        :param log_path: Path to the log file.
        :type log_path: ``str``
        """
        if os.path.exists(log_path):
            self._file_inode = os.stat(log_path).st_ino
        else:
            with open(log_path, "w+") as log:
                self._file_inode = os.stat(log.name).st_ino

        self._file_name = log_path
        self._file_position = LogFilePosition(self._file_inode, 0)

    @property
    def file_position(self) -> LogFilePosition:
        """Property for current log_path position."""
        return self._file_position

    def open_logfile_in_position(
        self, file_position: LogFilePosition, mode: str
    ):
        """
        Opens and returns a file handle for the file position passed. Sets the position
        to the specified file_position. Raises an Exception if the log_path to be opened
        does not exist or is corrupted.
        """
        try:
            file_handle = open(self._file_name, mode)
            file_handle.seek(file_position.marker)
            return file_handle
        except IOError:
            raise Exception(
                f"Log path {self._file_name} does not exist or it's corrupted."
            )

    def get_position(self, file_handle=None) -> LogFilePosition:
        """Returns the current position for the given file handle"""
        return self.file_position.get_position(file_handle)

    def get_next_file(self, file_handle, mode=None, affect_position=True):
        """
        Returns the same file handle since it has no rotation. Set ``affect_position``
        to False in situations where you want to get next file without altering
        the current file position.
        """
        if affect_position:
            self.file_position.marker = file_handle.tell()
            file_handle.seek(self.file_position.marker)
        else:
            file_handle.seek(file_handle.tell())
        return file_handle

    def get_inode_and_marker(self, file_handle) -> tuple:
        """Returns the inode and marker for the given file handle"""
        marker = file_handle.tell()
        return self._file_inode, marker

    def seek_eof(self) -> LogFilePosition:
        """Returns the end position of the log file."""
        position = self.get_end_of_file_position()
        return self.file_position.seek_position(position)

    def seek(self, mark=None) -> LogFilePosition:
        """
        Sets file position to the specified mark. The mark has to exist.
        If the mark is None sets file position to beginning of log file.
        """
        if mark:
            return self.file_position.seek_position(mark)

        position = self.get_start_of_file_position()
        return self.file_position.seek_position(position)

    def get_end_of_file_position(self) -> LogFilePosition:
        """Returns the end position for the log file."""
        marker = 0
        with open(self._file_name, "r") as f:
            f.seek(0, os.SEEK_END)
            marker = f.tell()

        return LogFilePosition(self._file_inode, marker)

    def get_start_of_file_position(self) -> LogFilePosition:
        """Returns the start position for the log file."""
        return LogFilePosition(self._file_inode, 0)


class LogMatcher(logger.Loggable):
    """
    Single line matcher for text files (usually log files). Once matched, it
    remembers the line number of the match and subsequent matches are scanned
    from the current line number. This can be useful when matched lines are not
    unique for the entire log file.
    """

    def __init__(self, log_path, strategy=NoLogRotationStrategy):
        """
        :param log_path: Path to the log file.
        :type log_path: ``str``
        """
        self.log_path = log_path
        self.marks = {}
        self.strategy = strategy(log_path)
        self.position = self.strategy.file_position
        super(LogMatcher, self).__init__()

    def seek(self, mark: Optional[str] = None):
        """
        Sets current file position to the specified mark. The mark has to exist.
        If the mark is None sets current file position to beginning of file.

        :param mark: Name of the mark.
        """
        if mark is None:
            self.position = self.strategy.seek()
        else:
            self.position = self.strategy.seek(self.marks[mark])

    def seek_eof(self):
        """Sets current file position to the current end of file."""
        self.position = self.strategy.seek_eof()

    def seek_sof(self):
        """Sets current file position to the start of file."""
        self.seek()

    def mark(self, name: str):
        """
        Marks the current file position with the specified name. The mark name
        can later be used to set the file position

        :param name: Name of the mark.
        """
        position = self.strategy.get_position()
        self.marks[name] = LogFilePosition(
            position.file_inode, position.marker
        )

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

        # As a convenience, we create the compiled regex if a string was
        # passed.
        if not hasattr(regex, "match"):
            regex = re.compile(regex)
        if isinstance(regex.pattern, str):
            read_mode = "r"

        log = self.strategy.open_logfile_in_position(self.position, read_mode)
        while True:
            line = log.readline()
            if line:
                match = regex.match(line)
                if match:
                    break
            else:
                time.sleep(LOG_MATCHER_INTERVAL)
                if time.time() > end_time:
                    break

                log = self.strategy.get_next_file(log, read_mode)

        self.position = self.strategy.get_position(log)

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

        # As a convenience, we create the compiled regex if a string was
        # passed.
        if not hasattr(regex, "match"):
            regex = re.compile(regex)
        if isinstance(regex.pattern, str):
            read_mode = "r"

        try:
            start_position = self.marks[mark1]
            end_position = self.marks[mark2]

            log = self.strategy.open_logfile_in_position(
                start_position, read_mode
            )
            current_inode, current_marker = self.strategy.get_inode_and_marker(
                log
            )

            while (end_position.file_inode != current_inode) or (
                end_position.marker > current_marker
            ):
                line = log.readline()
                if line:
                    match = regex.match(line)
                    if match:
                        break
                else:
                    log = self.strategy.get_next_file(
                        log, read_mode, affect_position=False
                    )

                (
                    current_inode,
                    current_marker,
                ) = self.strategy.get_inode_and_marker(log)

            return match
        except KeyError:
            raise ValueError(f'Mark "{mark1}" or "{mark2}" does not exist')

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

    def get_between(self, mark1=None, mark2=None, timeout=5):
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
        :param timeout: Timeout in seconds to find out all matches in file,
            defaults to 5 seconds.
        :type timeout: ``int``
        :return: The content between mark1 and mark2.
        :rtype: ``str``
        """
        start_time = time.time()
        end_time = start_time + timeout

        try:
            if mark1 is not None and mark2 is not None:
                if (
                    self.marks[mark1].file_inode
                    == self.marks[mark2].file_inode
                ) and (self.marks[mark1].marker >= self.marks[mark2].marker):
                    raise ValueError(
                        f'Mark "{mark1}" must be present before mark "{mark2}"'
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

            log = self.strategy.open_logfile_in_position(start_position, "r")
            current_inode, current_marker = self.strategy.get_inode_and_marker(
                log
            )

            while (end_position.file_inode != current_inode) or (
                end_position.marker > current_marker
            ):
                line = log.readline()
                if line:
                    lines_between.append(line)
                else:
                    # Timeout here is necessary for situations where rotation occurs and the user
                    # mistakenly swaps mark2 for mark1. Search is started from mark2 and while condition
                    # cannot be met. This is to end the search.
                    time.sleep(LOG_MATCHER_INTERVAL)
                    if time.time() > end_time:
                        break
                    log = self.strategy.get_next_file(
                        log, "r", affect_position=False
                    )

                (
                    current_inode,
                    current_marker,
                ) = self.strategy.get_inode_and_marker(log)

            return "".join(lines_between)
        except KeyError:
            raise ValueError(f'Mark "{mark1}" or "{mark2}" does not exist')
