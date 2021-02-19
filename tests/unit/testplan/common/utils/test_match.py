import os
import re
import itertools
import tempfile

import pytest

from testplan.common.utils.match import LogMatcher, match_regexps_in_file
from testplan.common.utils import timing


@pytest.yield_fixture(scope="module")
def basic_logfile():
    """Write a very small logfile for basic functional testing."""
    log_lines = ["first\n", "second\n", "third\n", "fourth\n", "fifth\n"]

    with tempfile.NamedTemporaryFile("w", delete=False) as logfile:
        logfile.writelines(log_lines)
        logfile.flush()
        filepath = logfile.name

    yield filepath
    os.remove(filepath)


@pytest.yield_fixture(scope="module")
def large_logfile():
    """Write a larger logfile for more realistic performance testing."""
    with tempfile.NamedTemporaryFile("w", delete=False) as logfile:
        # Write 1 million lines of 'blah' followed by one line 'Match me!'.
        logfile.writelines("blah\n" for _ in range(int(1e6)))
        logfile.write("Match me!\n")
        logfile.flush()
        filepath = logfile.name

    yield filepath
    os.remove(filepath)


class TestMatchRegexpsInFile(object):
    """
    Test the match_regexps_in_file function
    """

    def test_string(self, basic_logfile):
        log_extracts = [
            re.compile(r"(?P<first>first)"),
            re.compile(r"(?P<second>second)"),
        ]

        status, values = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], str)
        assert isinstance(values["second"], str)

    def test_bytes(self, basic_logfile):
        log_extracts = [
            re.compile(br"(?P<first>first)"),
            re.compile(br"(?P<second>second)"),
        ]

        status, values = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], bytes)
        assert isinstance(values["second"], bytes)

    def test_mixture(self, basic_logfile):
        log_extracts = [
            re.compile(r"(?P<first>first)"),
            re.compile(br"(?P<second>second)"),
        ]

        status, values = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], bytes)
        assert isinstance(values["second"], bytes)


class TestLogMatcher(object):
    """
    Test the LogMatcher class.
    """

    def test_match_found(self, basic_logfile):
        """Can the LogMatcher find the correct line in the log file."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(r"second")
        match = matcher.match(regex=regex_exp)

        assert match is not None
        assert match.group(0) == "second"

    def test_binary_match_found(self, basic_logfile):
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(b"second")
        match = matcher.match(regex=regex_exp)

        assert match is not None
        assert match.group(0) == b"second"

    def test_match_only_searches_after_position(self, basic_logfile):
        """
        LogMatcher should only search the text after the position, therefore it
        shouldn't find any successful matches for strings that appear before
        position x.
        """
        matcher = LogMatcher(log_path=basic_logfile)
        second_string = re.compile(r"second")
        match = matcher.match(regex=second_string)

        # It should find this string.
        assert match is not None
        assert match.group(0) == "second"

        # It shouldn't find this string as it has moved past this position.
        first_string = re.compile(r"first")
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=first_string, timeout=0.5)

    def test_match_not_found(self, basic_logfile):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(r"bob")
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=regex_exp, timeout=0.5)

    def test_binary_match_not_found(self, basic_logfile):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(b"bob")
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=regex_exp, timeout=0.5)

    def test_not_match(self, basic_logfile):
        """Does the LogMatcher raise an exception when match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        matcher.not_match(regex=re.compile(r"bob"), timeout=0.5)
        matcher.seek()
        with pytest.raises(Exception):
            matcher.not_match(regex=re.compile(r"third"), timeout=0.5)

    def test_match_all(self, basic_logfile):
        """Can the LogMatcher find all the correct lines in the log file."""
        matcher = LogMatcher(log_path=basic_logfile)
        matches = matcher.match_all(regex=re.compile(r".+ir.+"), timeout=0.5)
        assert len(matches) == 2
        assert matches[0].group(0) == "first"
        assert matches[1].group(0) == "third"
        matcher.seek()
        matches = matcher.match_all(regex=re.compile(r".+th.*"), timeout=0.5)
        assert len(matches) == 2
        assert matches[0].group(0) == "fourth"
        assert matches[1].group(0) == "fifth"

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
        match = matcher.match(regex=r"^Match me!$", timeout=10)

        assert match is not None
        assert match.group(0) == "Match me!"
