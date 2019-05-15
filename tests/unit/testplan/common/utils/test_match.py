import os
import re
import itertools
import tempfile

import pytest

from testplan.common.utils.match import LogMatcher
from testplan.common.utils import timing

@pytest.yield_fixture(scope='module')
def basic_logfile():
    """Write a very small logfile for basic functional testing."""
    log_lines = [
        'first\n',
        'second\n',
        'third\n',
        'fourth\n',
        'fifth\n']

    with tempfile.NamedTemporaryFile('w', delete=False) as logfile:
        logfile.writelines(log_lines)
        filepath = logfile.name

    yield filepath
    os.remove(filepath)


@pytest.yield_fixture(scope='module')
def large_logfile():
    """Write a larger logfile for more realistic performance testing."""
    with tempfile.NamedTemporaryFile('w', delete=False) as logfile:
        # Write 1 million lines of 'blah' followed by one line 'Match me!'.
        logfile.writelines('blah\n' for _ in  range(int(1e6)))
        logfile.write('Match me!\n')
        filepath = logfile.name

    yield filepath
    os.remove(filepath)


class TestLogMatcher(object):
    """
    Test the LogMatcher class.
    """

    def test_match_found(self, basic_logfile):
        """Can the LogMatcher find the correct line in the log file."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(r'second')
        match = matcher.match(regex=regex_exp)

        assert match is not None
        assert match.group(0) == 'second'

    def test_match_only_searches_after_position(self, basic_logfile):
        """
        LogMatcher should only search the text after the position, therefore it
        shouldn't find any successful matches for strings that appear before
        position x.
        """
        matcher = LogMatcher(log_path=basic_logfile)
        second_string = re.compile(r'second')
        match = matcher.match(regex=second_string)

        # It should find this string.
        assert match is not None
        assert match.group(0) == 'second'

        # It shouldn't find this string as it has moved past this position.
        first_string = re.compile(r'first')
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=first_string, timeout=0.5)

    def test_match_not_found(self, basic_logfile):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(r'bob')
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=regex_exp, timeout=0.5)

    def test_match_large_file(self, large_logfile):
        """
        Test matching the last entry in a large logfile, as a more realistic
        test. The LogMatcher should quickly iterate through lines in the
        logfile and return the match without timing out.
        """
        matcher = LogMatcher(log_path=large_logfile)

        # Check that the LogMatcher can find the last 'Match me!' line in a
        # reasonable length of time. 10s is a very generous timeout, most
        # of the time it should complete in <1s.
        match = matcher.match(regex=r'^Match me!$', timeout=10)

        assert match is not None
        assert match.group(0) == 'Match me!'

