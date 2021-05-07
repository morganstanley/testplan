"""
Module of utility types and functions that perform matching.
"""
import os
import time
import re

from . import timing
from . import logger

LOG_MATCHER_INTERVAL = 0.25


def match_regexps_in_file(logpath, log_extracts, return_unmatched=False):
    """
    Return a boolean, dict pair indicating whether all log extracts matches,
    as well as any named groups they might have matched.

    :param logpath: Log file path.
    :type logpath: ``str``
    :param log_extracts:  Regex list.
    :type log_extracts: ``Union[bytes, str]``
    :param return_unmatched: Flag for return unmatched regex. Default: False
    :type return_unmatched: ``bool```
    :return: Match result.
    :rtype: ``tuple``

    """
    extracted_values = {}

    if not os.path.exists(logpath):
        if return_unmatched:
            return False, extracted_values, log_extracts
        return False, extracted_values

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

    if return_unmatched:
        unmatched = [
            exc
            for idx, exc in enumerate(log_extracts)
            if not extracts_status[idx]
        ]
        return all(extracts_status), extracted_values, unmatched
    return all(extracts_status), extracted_values


class LogMatcher(logger.Loggable):
    """
    Single line matcher for text files (usually log files). Once matched, it
    remembers the line number of the match and subsequent matches are scanned
    from the current line number. This can be useful when matched lines are not
    unique for the entire log file.
    """

    def __init__(self, log_path):
        """
        :param log_path: Path to the log file.
        :type log_path: ``str``
        """
        self.log_path = log_path
        self.position = 0
        self.marks = {}
        super(LogMatcher, self).__init__()

    def seek(self, mark=None):
        """
        Sets current file position to the specified mark. The mark has to exist.
        If the mark is None sets current file position to beginning of file.

        :param mark: Name of the mark.
        :type mark: ``str`` or ``NoneType``
        """
        if mark is None:
            self.position = 0
        else:
            self.position = self.marks[mark]

    def seek_eof(self):
        """Sets current file position to the current end of file."""
        with open(self.log_path, "r") as log:
            log.seek(0, os.SEEK_END)
            self.position = log.tell()

    def seek_sof(self):
        """Sets current file position to the start of file."""
        self.seek()

    def mark(self, name):
        """
        Marks the current file position with the specified name. The mark name
        can later be used to set the file position

        :param name: Name of the mark.
        :type name: ``str``
        """
        self.marks[name] = self.position

    def match(self, regex, timeout=5):
        """
        Matches each line in the log file from the current line number to the
        end of the file. If a match is found the line number is stored and the
        match is returned. If no match is found an exception is raised.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern, bytes]``
        :param timeout: Timeout in seconds to wait for matching process,
            0 means should not wait and return whatever matched on initial
            scan, defaults to 5 seconds
        :type timeout: ``int``
        :return: The regex match or raise an Exception if no match is found
        :rtype: ``re.Match``
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

        with open(self.log_path, read_mode) as log:
            log.seek(self.position)

            while match is None:
                line = log.readline()
                if line:
                    match = regex.match(line)
                    if match:
                        break
                else:
                    time.sleep(LOG_MATCHER_INTERVAL)
                    if time.time() > end_time:
                        break

            self.position = log.tell()

        if match is None:
            raise timing.TimeoutException(
                "No match[{}] found in {}s".format(regex.pattern, timeout)
            )
        else:
            self.logger.debug(
                "Match[%s] found in %.2fs",
                regex.pattern,
                time.time() - start_time,
            )

        return match

    def not_match(self, regex, timeout=5):
        """
        Opposite of :py:meth:`~testplan.common.utils.match.LogMatcher.match`
        which raises an exception if a match is found. Matching is performed
        from the current file position. If match is not found within timeout
        period then no exception is raised.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern, bytes]``
        :param timeout: Timeout in seconds to wait for matching process,
            0 means should not wait and return whatever matched on initial
            scan, defaults to 5 seconds
        :type timeout: ``int``
        """
        match = None

        try:
            match = self.match(regex, timeout)
        except timing.TimeoutException:
            pass

        if match:
            raise Exception(
                "Unexpected match[{}] found in {}s".format(
                    regex.pattern, timeout
                )
            )

    def match_all(self, regex, timeout=5):
        """
        Similar to match, but returns all occurrences of regex. If no match
        is found till timeout an Exception is raised.

        :param regex: Regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern, bytes]``
        :param timeout: Timeout in seconds to find out all matches in file,
            defaults to 5 seconds.
        :type timeout: ``int``
        :return: The regex match or raise an exception if no match is found
        :rtype: ``re.Match``
        """
        matches = []
        end_time = time.time() + timeout

        try:
            while timeout >= 0:
                matches.append(self.match(regex, timeout))
                timeout = end_time - time.time()
        except timing.TimeoutException:
            if not matches:
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

        with open(self.log_path, read_mode) as log:
            log.seek(self.marks[mark1] if mark1 is not None else 0)
            endpos = self.marks[mark2]
            while endpos > log.tell():
                line = log.readline()
                if not line:
                    break
                match = regex.match(line)
                if match:
                    break

        return match

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
        if mark1 is not None and mark2 is not None:
            if self.marks[mark1] >= self.marks[mark2]:
                raise ValueError(
                    'Mark "{}" must be present before mark "{}"'.format(
                        mark1, mark2
                    )
                )

        with open(self.log_path, "r") as log:
            start_pos = self.marks[mark1] if mark1 is not None else 0
            end_pos = self.marks[mark2] if mark2 is not None else None
            log.seek(start_pos)
            if not end_pos:
                return log.read()
            lines_between = []
            while end_pos > log.tell():
                line = log.readline()
                lines_between.append(line)
            return "".join(lines_between)
