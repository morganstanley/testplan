"""String manipulation utilities."""

import sys

import re
import os
import unicodedata
import textwrap
import six

import colorama
colorama.init()
from termcolor import colored


_DESCRIPTION_CUTOFF_REGEX = re.compile(r'^(\s|\t)+')


def format_description(description):
    """
    Get rid of empty lines and unindent multiline text until
    the leftmost indented line has no whitespaces on the left.

    In:

      (assume dots represent whitespace)

        ....Hello world
        ......Foo bar
        <EMPTY-LINE>
        ....1 2 3 4

    Out:

        Hello World
        ..Foo bar
        1 2 3 4
    """
    lines = [line for line in description.split(os.linesep) if line.strip()]
    matches = [_DESCRIPTION_CUTOFF_REGEX.match(line) for line in lines]
    if matches:
        min_offset = \
            min(match.end() if match is not None else 0 for match in matches)
        return os.linesep.join([line[min_offset:] for line in lines])
    return ''


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    :param value: string value to slugify
    :type value: ``str``

    :return: slugified string value, suitable as a directory or filename
    :rtype: ``str``
    """
    if sys.hexversion >= 0x30303f0:
        value = unicodedata.normalize('NFKD',
                                      value).encode('ascii', 'ignore')
        value = re.sub(br'[^\w\s-]', b'', value).strip().lower()
        return re.sub(br'[-\s]+', b'-', value).decode('ascii')
    else:
        value = unicodedata.normalize(
            'NFKD',
            six.text_type(value)
        ).encode('ascii', 'ignore')
        value = six.text_type(re.sub(r'[^\w\s-]', '', value).strip().lower())
        return str(re.sub(r'[-\s]+', '-', value))


class Color(object):
    """Utility class with shortcuts for colored console output."""

    @staticmethod
    def colored(msg, color):
        return colored(msg, color)

    @staticmethod
    def green(msg):
        return colored(msg, 'green')

    @staticmethod
    def red(msg):
        return colored(msg, 'red')

    @staticmethod
    def yellow(msg):
        return colored(msg, 'yellow')

    @staticmethod
    def passed(msg=None, check=None):
        if msg is None:
            msg = 'Pass' if check else 'Fail'

        if callable(check):
            check = check()
        return Color.green(msg) if check else Color.red(msg)


INDENT_REGEX = re.compile('^\s*')


def wrap(text, width=150):
    """
    Wraps `text` within given `width` limit, keeping initial indentation of
    each line (and generated lines). Useful for wrapping exception messages.

    :param text: Text to be wrapped.
    :param width: Maximum character limit for each line.
    :return: Wrapped text
    """
    wrapper = textwrap.TextWrapper(width=width, replace_whitespace=False)
    text_ctx = [wrapper.wrap(t) for t in text.splitlines()]

    result = []
    for line_list in text_ctx:
        first, rest = line_list[0], line_list[1:]
        indent_match = INDENT_REGEX.match(first)
        if indent_match:
            prefix = ' ' * (indent_match.end() - indent_match.start())
            result.extend(
                [first] + ['{}{}'.format(prefix, line) for line in rest])
        else:
            result.extend(line_list)
    return os.linesep.join(result)
