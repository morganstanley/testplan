"""
Module of utility types and functions that perform matching.
"""
import os


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


class LogMatcher(object):
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
        self.line_no = 0

    def match(self, regex):
        """
        Matches each line in the log file from the current line number to the
        end of the file. If a match is found the line number is stored and the
        match is returned. If no match is found an Exception is raised.

        :param regex: compiled regular expression (``re.compile``)
        :type regex: ``re.Pattern``

        :return: The regex match or raise an Exception if no match is found.
        :rtype: ``re.Match``
        """
        with open(self.log_path, 'r') as log:
            lines = log.readlines()
            for line_no, line in enumerate(lines[self.line_no:], self.line_no):
                match = regex.match(line)
                if match:
                    self.line_no = line_no + 1
                    return match

        raise ValueError('No matches found')
