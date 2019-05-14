"""
Module of utility types and functions that perform matching.
"""
import os
import time

from . import timing
from . import logger

LOG_MATCHER_INTERVAL = 0.25


def match_regexps_in_file(logpath, log_extracts, return_unmatched=False):
    """
    Return a boolean, dict pair indicating whether all log extracts matches,
    as well as any named groups they might have matched.
    """
    extracted_values = {}

    if not os.path.exists(logpath):
        if return_unmatched:
            return False, extracted_values, log_extracts
        return False, extracted_values

    extracts_status = [False for _ in log_extracts]

    with open(logpath, 'r') as log:
        for line in log:
            for pos, regexp in enumerate(log_extracts):
                match = regexp.match(line)
                if match:
                    extracted_values.update(match.groupdict())
                    extracts_status[pos] = True

    if return_unmatched:
        unmatched = [
            exc for idx, exc in enumerate(log_extracts)
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

        :param regex: compiled regular expression (``re.compile``)
        :type regex: ``re.Pattern``

        :return: The regex match or raise an Exception if no match is found.
        :rtype: ``re.Match``
        """
        match = None
        start_time = time.time()
        end_time = start_time + timeout

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
            self.logger.debug('Match found in %ds', time.time() - start_time)
        return match

