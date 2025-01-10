import os
import re
import tempfile
import time
from unittest import mock

import pytest

from testplan.common.utils import timing
from testplan.common.utils.match import LogMatcher, match_regexps_in_file


@pytest.fixture(
    params=[True, False], ids=["With log rotation", "Without log rotation"]
)
def test_rotation(request):
    return request.param


@pytest.fixture
def basic_logfile(rotating_logger, test_rotation):
    """Write a very small logfile for basic functional testing."""
    log_lines = ["first", "second", "third", "fourth", "fifth"]

    for i, line in enumerate(log_lines):
        rotating_logger.info(line)
        if test_rotation and i % 2:
            rotating_logger.doRollover()
            time.sleep(0.01)  # to get the mtime to be different

    return rotating_logger.pattern if test_rotation else rotating_logger.path


@pytest.fixture(scope="module")
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


class TestMatchRegexpsInFile:
    """
    Test the match_regexps_in_file function
    """

    @pytest.fixture
    def basic_logfile(self, test_rotation, basic_logfile):
        if test_rotation:
            pytest.skip()
        return basic_logfile

    def test_string(self, basic_logfile):
        log_extracts = [
            re.compile(r"(?P<first>first)"),
            re.compile(r"(?P<second>second)"),
        ]

        status, values, _ = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], str)
        assert isinstance(values["second"], str)

    def test_bytes(self, basic_logfile):
        log_extracts = [
            re.compile(rb"(?P<first>first)"),
            re.compile(rb"(?P<second>second)"),
        ]

        status, values, _ = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], bytes)
        assert isinstance(values["second"], bytes)

    def test_mixture(self, basic_logfile):
        log_extracts = [
            re.compile(r"(?P<first>first)"),
            re.compile(rb"(?P<second>second)"),
        ]

        status, values, _ = match_regexps_in_file(basic_logfile, log_extracts)
        assert status is True
        assert isinstance(values["first"], bytes)
        assert isinstance(values["second"], bytes)


LOG_MATCHER_TIMEOUT = 0.1


@mock.patch("testplan.common.utils.match.LOG_MATCHER_INTERVAL", 0.02)
class TestLogMatcher:
    """
    Test the LogMatcher class.
    """

    def test_match_found(self, basic_logfile):
        """Can the LogMatcher find the correct line in the log file."""
        matcher = LogMatcher(log_path=basic_logfile)
        regex_exp = re.compile(r"second")
        match = matcher.match(regex=regex_exp)
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3

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
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3

        # It should find this string.
        assert match is not None
        assert match.group(0) == "second"

        # It shouldn't find this string as it has moved past this position.
        first_string = re.compile(r"first")
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=first_string, timeout=LOG_MATCHER_TIMEOUT)

        # When `timeout` is set to zero, it should return None without raising exception.
        assert matcher.match(regex=first_string, timeout=0) is None
        # Same applies when `raise_on_timeout` is set to false.
        assert (
            matcher.match(
                regex=first_string,
                timeout=LOG_MATCHER_TIMEOUT,
                raise_on_timeout=False,
            )
            is None
        )

    def test_match_not_found(self, basic_logfile):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=r"bob", timeout=LOG_MATCHER_TIMEOUT)
            assert len(matcher._debug_info_s) == 3
            assert len(matcher._debug_info_e) == 3

    def test_binary_match_not_found(self, basic_logfile):
        """Does the LogMatcher raise an exception when no match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        with pytest.raises(timing.TimeoutException):
            matcher.match(regex=b"bob", timeout=LOG_MATCHER_TIMEOUT)

    def test_not_match(self, basic_logfile):
        """Does the LogMatcher raise an exception when match is found."""
        matcher = LogMatcher(log_path=basic_logfile)
        matcher.not_match(
            regex=re.compile(r"bob"), timeout=LOG_MATCHER_TIMEOUT
        )
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3
        matcher.seek()
        with pytest.raises(Exception, match=r"^Unexpected match.*"):
            matcher.not_match(
                regex=re.compile(r"third"), timeout=LOG_MATCHER_TIMEOUT
            )
            assert len(matcher._debug_info_s) == 3
            assert len(matcher._debug_info_e) == 3
        with pytest.raises(Exception, match=r"^Unexpected match.*"):
            matcher.not_match(regex=re.compile(r"fourth"), timeout=0)
            assert len(matcher._debug_info_s) == 3
            assert len(matcher._debug_info_e) == 3

    def test_match_all(self, basic_logfile):
        """Can the LogMatcher find all the correct lines in the log file."""
        matcher = LogMatcher(log_path=basic_logfile)
        matches = matcher.match_all(
            regex=re.compile(r".+ir.+"), timeout=LOG_MATCHER_TIMEOUT
        )
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3
        assert len(matches) == 2
        assert matches[0].group(0) == "first"
        assert matches[1].group(0) == "third"
        matcher.seek()
        matches = matcher.match_all(
            regex=re.compile(r".+th.*"), timeout=LOG_MATCHER_TIMEOUT
        )
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3
        assert len(matches) == 2
        assert matches[0].group(0) == "fourth"
        assert matches[1].group(0) == "fifth"

    def test_match_all_not_found(self, basic_logfile):
        """Does the LogMatcher behave properly when no match exists."""
        matcher = LogMatcher(log_path=basic_logfile)
        matches = matcher.match_all(
            regex=r".+th.+",
            timeout=LOG_MATCHER_TIMEOUT,
            raise_on_timeout=False,
        )
        assert not len(matches)
        matcher.seek()
        with pytest.raises(timing.TimeoutException):
            matcher.match_all(regex=r".+th.+", timeout=LOG_MATCHER_TIMEOUT)

    def test_match_all_large(self, large_logfile):
        matcher = LogMatcher(log_path=large_logfile)
        matcher.match_all(r"blah", timeout=0.5)
        assert len(matcher._debug_info_s) == 3
        assert len(matcher._debug_info_e) == 3
        assert matcher._debug_info_e[2] == "blah\n"

    def test_match_between(self, basic_logfile):
        """
        Does the LogMatcher match between the given marks.
        """
        matcher = LogMatcher(log_path=basic_logfile)
        matcher.match(regex=re.compile(r"second"))
        matcher.mark("start")
        matcher.match(regex=re.compile(r"fourth"))
        matcher.mark("end")

        match = matcher.match_between(r"third", "start", "end")
        assert match.group(0) == "third"
        match = matcher.match_between(r"fourth", "start", "end")
        assert match.group(0) == "fourth"
        assert matcher.match_between(r"second", "start", "end") is None
        assert matcher.match_between(r"fifth", "start", "end") is None

    def test_not_match_between(self, basic_logfile):
        """
        Does the LogMatcher return True when match is found
        between the given marks.
        """
        matcher = LogMatcher(log_path=basic_logfile)
        matcher.match(regex=re.compile(r"second"))
        matcher.mark("start")
        matcher.match(regex=re.compile(r"fourth"))
        matcher.mark("end")
        assert matcher.not_match_between(r"fifth", "start", "end")
        assert not matcher.not_match_between(r"third", "start", "end")

    @pytest.mark.parametrize("is_binary", [True, False])
    def test_get_between(self, basic_logfile, is_binary):
        """Does the LogMatcher return the required content between marks."""

        def binary_or_string(value):
            return value.encode() if is_binary else value

        matcher = LogMatcher(log_path=basic_logfile, binary=is_binary)
        matcher.match(regex=re.compile(binary_or_string("second")))
        matcher.mark("start")
        matcher.match(regex=re.compile(binary_or_string("fourth")))
        matcher.mark("end")

        newline = os.linesep.encode() if is_binary else "\n"
        lines = [
            binary_or_string(line)
            for line in ["first", "second", "third", "fourth", "fifth"]
        ]

        def construct_expected(slice):
            return newline.join(slice) + newline

        content = matcher.get_between()
        assert content == construct_expected(lines)
        content = matcher.get_between(None, "end")
        assert content == construct_expected(lines[:4])
        content = matcher.get_between("start", None)
        assert content == construct_expected(lines[2:])
        content = matcher.get_between("start", "end")
        assert content == construct_expected(lines[2:4])

    def test_match_large_file(self, large_logfile):
        """
        Test matching the last entry in a large logfile, the LogMatcher
        shall iterate through lines in the logfile regardless of too small a timeout.
        This avoids false alert when log file reading is slow due to machine load.
        """
        matcher = LogMatcher(log_path=large_logfile)

        # Check that the LogMatcher can find the last 'Match me!' line with
        # a whole-file scan.
        match = matcher.match(
            regex=r"^Match me!$", timeout=0, raise_on_timeout=False
        )

        assert match is not None
        assert match.group(0) == "Match me!"

        matcher.seek()

        # Check that the LogMatcher will reach EOF regardless of timeout
        match = matcher.match(
            regex=r"^Match me!$", timeout=0.01, raise_on_timeout=False
        )

        assert match is not None
        assert match.group(0) == "Match me!"

    def test_scoped_match(self, rotating_logger, test_rotation):
        """unit test for expect api"""

        if test_rotation and os.name != "posix":
            pytest.skip("rotating log handler doesn't really support windows")

        matcher = LogMatcher(
            log_path=rotating_logger.pattern
            if test_rotation
            else rotating_logger.path
        )
        drinks = [
            "black tea",
            "oolong tea",
            "whisky",
            "rum",
            "vodka",
            "green tea",
        ]
        with matcher.expect(r"green tea") as scoped:
            s_pos = matcher.position
            for i, d in enumerate(drinks):
                rotating_logger.info(d)
                if test_rotation and i % 3 == 1:
                    rotating_logger.doRollover()
                    # NOTE: time for fs sync,
                    # NOTE: otherwise we can have logfiles with same mtime
                    time.sleep(0.1)
        assert len(scoped.match_results) == 1
        assert scoped.match_failure is None

        e_pos = matcher.position
        matcher.seek_eof()
        assert e_pos == matcher.position
        if test_rotation:
            assert e_pos.inode != s_pos.inode

    # NOTE: following code could be useful for a future pr
    # @pytest.mark.parametrize(
    #     "is_in_order", (True, False), ids=("in order", "out of order")
    # )
    # def test_scoped_match(self, rotating_logger, test_rotation, is_in_order):
    #     """unit test for expect api"""
    #     matcher = LogMatcher(
    #         log_path=rotating_logger.pattern
    #         if test_rotation
    #         else rotating_logger.path
    #     )
    #     if is_in_order:
    #         drinks = [
    #             "green tea",
    #             "black tea",
    #             "oolong tea",
    #             "whisky",
    #             "rum",
    #             "vodka",
    #         ]
    #     else:
    #         drinks = [
    #             "green tea",
    #             "whisky",
    #             "vodka",
    #             "oolong tea",
    #             "black tea",
    #             "rum",
    #         ]
    #
    #     with matcher.expect(
    #         [r"green tea", r"oolong tea", r"vodka"], strict_order=is_in_order
    #     ) as scope:
    #         s_pos = matcher.position
    #         for i, d in enumerate(drinks):
    #             rotating_logger.info(d)
    #             if test_rotation and i % 3 == 1:
    #                 rotating_logger.doRollover()
    #                 # NOTE: time for fs sync,
    #                 # NOTE: otherwise we can have logfiles with same mtime
    #                 time.sleep(0.1)
    #
    #     assert len(scope.match_results) == 3
    #     assert scope.match_failure is None
    #
    #     e_pos = matcher.position
    #     if is_in_order:
    #         matcher.seek_eof()
    #         assert e_pos == matcher.position
    #     elif test_rotation:
    #         assert e_pos.inode != s_pos.inode
    #         matcher.seek_eof()
    #         assert e_pos.inode != matcher.position.inode
    #     else:
    #         assert e_pos.position > s_pos.position
    #         matcher.seek_eof()
    #         assert e_pos.position < matcher.position.position
