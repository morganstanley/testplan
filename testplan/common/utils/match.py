"""
Module of utility types and functions that perform matching.
"""
import os
import time
import re

from . import timing
from . import logger

LOG_MATCHER_INTERVAL = 0.25


def wait_match_regexps_in_file(log_path, log_extracts, timeout=5):
    """
    Wait for all regexps to be matched in a file.

    :param log_path: Path to the file to match
    :type log_path: ``str``
    :param log_extracts: Regular expressions to search in each log. A list of
        either strings or compiled regex objects may be used.
    :type log_extracts: ``List[Union[str, re.Pattern]]``
    :param timeout: Timeout applied to each regexp individually.
    :type timeout ``int``

    :raises timing.TimeoutException: if the log regexps aren't matched within
        the configured timeout.

    :return: dictionary of extracted values for named groups.
    :rtype: ``Dict[str, str]``
    """
    extracted_values = {}

    # Before attempting to match any log regexps, wait for the file to be
    # created. This helps to avoid a race condition if this function is called
    # immediately after a process that writes logs is started.
    err_msg = 'File not found at {}'.format(log_path)
    for _ in timing.get_sleeper(interval=LOG_MATCHER_INTERVAL,
                                timeout=timeout,
                                raise_timeout_with_msg=err_msg):
        if os.path.isfile(log_path):
            break

    # Match each log regex in turn. Note that we use a new LogMatcher instance
    # for each regex: the effect of this is that we will iterate through the
    # logfile from the start for each regex. If we could guarantee that the
    # order of logs matched is deterministic we could optimize by using a
    # single LogMatcher which remembers the position of each previous match.
    # While a little inefficient, this approach is more flexible as the
    # order of the regexps given does not matter greatly.
    for i, regexp in enumerate(log_extracts):
        matcher = LogMatcher(log_path)
        try:
            match = matcher.match(regexp, timeout=timeout)
            extracted_values.update(match.groupdict())
        except timing.TimeoutException:
            unmatched = log_extracts[i:]
            raise timing.TimeoutException(
                'Timed out after {timeout}s waiting to match regexps in file '
                '{file}.\nUnmatched regexps: {unmatched}'
                .format(timeout=timeout, file=log_path, unmatched=unmatched))

    return extracted_values


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
        :type mark: ``str`` or ``None``
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
        match is returned. If no match is found an Exception is raised.

        :param regex: regex string or compiled regular expression
            (``re.compile``)
        :type regex: ``Union[str, re.Pattern]``

        :return: The regex match or raise an Exception if no match is found.
        :rtype: ``re.Match``
        """
        match = None
        start_time = time.time()
        end_time = start_time + timeout

        # As a convenience, we create the compiled regex if a string was
        # passed.
        if not hasattr(regex, 'match'):
            regex = re.compile(regex)

        with open(self.log_path, 'r') as log:
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
                'No matches found in {}s'.format(timeout))
        else:
            self.logger.debug('Match found in %.2fs', time.time() - start_time)
        return match

