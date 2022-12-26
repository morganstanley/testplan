"""String manipulation utilities."""

import os
import re
import inspect
import uuid
import unicodedata
import textwrap

import colorama

colorama.init()
from termcolor import colored

from reportlab.pdfbase.pdfmetrics import stringWidth


_DESCRIPTION_CUTOFF_REGEX = re.compile(r"^(\s|\t)+")


def map_to_str(value):
    """
    Convert bytes to str byte-by-byte
    """

    if isinstance(value, bytes):
        return "".join(map(chr, value))
    else:
        return value


def to_str(value, encoding="utf-8", errors="strict"):
    """
    Coerce a string to ``str`` type.

    :param value: A string to be converted
    :type value: ``str`` or ``bytes``
    :param encoding: Encoding method
    :type encoding: ``str``
    :param errors: Error handling scheme
    :type errors: ``str``
    :return: Converted unicode string.
    :rtype: ``str``
    """
    if isinstance(value, bytes):
        return value.decode(encoding, errors)
    if isinstance(value, str):
        return value
    else:
        raise TypeError(f"Unexpected type '{type(value)}'")


def to_bytes(value, encoding="utf-8", errors="strict"):
    """
    Coerce a string to ``bytes`` type.

    :param value: A string to be converted
    :type value: ``str`` or ``bytes``
    :param encoding: Encoding method
    :type encoding: ``str``
    :param errors: Error handling scheme
    :type errors: ``str``
    :return: Converted byte string.
    :rtype: ``bytes``
    """
    if isinstance(value, str):
        return value.encode(encoding, errors)
    if isinstance(value, bytes):
        return value
    else:
        raise TypeError(f"Unexpected type '{type(value)}'")


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
        min_offset = min(
            match.end() if match is not None else 0 for match in matches
        )
        return os.linesep.join([line[min_offset:] for line in lines])
    return ""


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    :param value: string value to slugify
    :type value: ``str``

    :return: slugified string value, suitable as a directory or filename
    :rtype: ``str``
    """
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = re.sub(rb"[^\w\s-]", b"", value).strip().lower()
    return re.sub(rb"[-\s]+", b"-", value).decode("ascii")


def uuid4():
    """
    Generate a globally unique id.

    :return: A string complied with `uuid.uuid4` format
    :rtype: ``str``
    """
    return str(uuid.uuid4())


class Color:
    """Utility class with shortcuts for colored console output."""

    @staticmethod
    def colored(msg, color):
        return colored(msg, color)

    @staticmethod
    def green(msg):
        return colored(msg, "green")

    @staticmethod
    def red(msg):
        return colored(msg, "red")

    @staticmethod
    def yellow(msg):
        return colored(msg, "yellow")

    @staticmethod
    def passed(msg=None, check=None):
        if msg is None:
            msg = "Pass" if check else "Fail"

        if callable(check):
            check = check()
        return Color.green(msg) if check else Color.red(msg)


INDENT_REGEX = re.compile(r"^\s*")


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
        if not line_list:
            return text
        first, rest = line_list[0], line_list[1:]
        indent_match = INDENT_REGEX.match(first)
        if indent_match:
            prefix = " " * (indent_match.end() - indent_match.start())
            result.extend(
                [first] + ["{}{}".format(prefix, line) for line in rest]
            )
        else:
            result.extend(line_list)
    return os.linesep.join(result)


def split_line(line, max_width, get_width_func=None):
    """
    Split `line` into multi-lines if width exceeds `max_width`.

    :param line: Line to be split.
    :param max_width: Maximum length of each line (unit: px).
    :param get_width_func: A function which computes width of string
                           according to font and font size.
    :return: list of lines
    """
    result = []
    total_width = 0
    tmp_str = ""
    get_text_width = (
        get_width_func
        if get_width_func
        else lambda text: stringWidth(text, "Helvetica", 9)
    )

    for ch in line:
        char_width = get_text_width(ch)
        if total_width + char_width <= max_width or not tmp_str:
            tmp_str += ch
            total_width += char_width
        else:
            result.append(tmp_str)
            tmp_str = ch
            total_width = char_width

    if tmp_str:
        result.append(tmp_str)

    return result


def split_text(
    text, font_name, font_size, max_width, keep_leading_whitespace=False
):
    """
    Wraps `text` within given `max_width` limit (measured in px), keeping
    initial indentation of each line (and generated lines) if
    `keep_leading_whitespace` is True.

    :param text: Text to be split.
    :param font_name: Font name.
    :param font_size: Font size.
    :param max_width: Maximum length of each line (unit: px).
    :param keep_leading_whitespace: each split line keeps the leading
                                    whitespace.
    :return: list of lines
    """

    def get_text_width(text, name=font_name, size=font_size):
        return stringWidth(text, name, size)

    result = []
    lines = [line for line in re.split(r"[\r\n]+", text) if line]

    for line in lines:
        line_list = split_line(line, max_width, get_text_width)
        if keep_leading_whitespace and len(line_list) > 1:
            first, rest = line_list[0], line_list[1:]
            indent_match = _DESCRIPTION_CUTOFF_REGEX.match(first)
            if indent_match:
                prefix = first[indent_match.start() : indent_match.end()]
                line_list = [first] + ["{}{}".format(prefix, s) for s in rest]
        result.extend(line_list)

    return os.linesep.join(result)


def indent(lines_str, indent_size=2):
    """
    Indent a multi-line string with a common indent.

    :param lines_str: Multi-line string.
    :type lines_str: ``str``
    :param indent_size: Number of spaces to indent by - defaults to 2.
    :type indent_size: ``int``
    :return: New string with extra indent.
    :rtype: ``str``
    """
    indent = " " * indent_size
    return "\n".join(
        "{indent}{line}".format(indent=indent, line=line)
        for line in lines_str.splitlines()
    )


def get_docstring(obj):
    """
    Get object docstring without leading whitespace.
    :param obj: Object to be extracted docstring.
    :type obj: ``object``
    :return: Docstring of the object.
    :rtype: ``str`` or ``NoneType``
    """
    if hasattr(obj, "__doc__"):
        if obj.__doc__:
            return inspect.cleandoc(obj.__doc__)
    return None
