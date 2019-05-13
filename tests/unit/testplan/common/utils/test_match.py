import os
import re
from mock import mock_open, patch

import pytest

from testplan.common.utils.match import LogMatcher

MATCH_OPEN_LIB = 'testplan.common.utils.match.open'
TMP_FILENAME = 'no_file.log'
LOG_LINES = [
    'fifth',
    'fourth',
    'third',
    'second',
    'first'
]
LOG_FILECONTENTS = '\n'.join(LOG_LINES)


class TestLogMatcher(object):
    """
    Test the LogMatcher class.
    """

    def test_match_found(self):
        """Can the LogMatcher find the correct line in the log file."""
        matcher = LogMatcher(log_path=TMP_FILENAME)
        regex_exp = re.compile(r'second')
        with patch(MATCH_OPEN_LIB,
                   mock_open(read_data=LOG_FILECONTENTS),
                   create=True):
            match = matcher.match(regex=regex_exp)

        assert match is not None

    def test_match_only_searches_after_position(self):
        """
        LogMatcher should only search the text after the position, therefore it
        shouldn't find any successful matches for strings that appear before
        position x.
        """
        matcher = LogMatcher(log_path=TMP_FILENAME)
        second_string = re.compile(r'second')
        with patch(MATCH_OPEN_LIB,
                   mock_open(read_data=LOG_FILECONTENTS),
                   create=True):
            match = matcher.match(regex=second_string)

        # It should find this string.
        assert match is not None

        # It shouldn't find this string as it has moved past this position.
        first_string = re.compile(r'first')
        with patch(MATCH_OPEN_LIB,
                   mock_open(read_data=LOG_FILECONTENTS),
                   create=True):
            with pytest.raises(ValueError):
                matcher.match(regex=first_string, timeout=0.5)

    def test_match_not_found(self):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=TMP_FILENAME)
        regex_exp = re.compile(r'bob')
        with patch(MATCH_OPEN_LIB,
                   mock_open(read_data=LOG_FILECONTENTS),
                   create=True):
            with pytest.raises(ValueError):
                matcher.match(regex=regex_exp, timeout=0.5)

