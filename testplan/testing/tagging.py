"""Generic Tagging logic."""

import re
import argparse
import functools
import collections


SAMPLE_ARGUMENTS = """tag1 tag2 tagname1=tag3,tag4 tagname2=tag5,tag6"""

SIMPLE = "simple"  # key for simple tags

# Both tag values and tag names cannot start & end with dash / underscore
# (for readable URL params)

# Currently allowing same patterns for tags and tag names
TAG_VALUE_PATTERN = r"(?![\s\_\-\)\(])[\w\s\-\(\)]+(?<![\s\_\-])"
TAG_NAME_PATTERN = TAG_VALUE_PATTERN

# Pattern for simple tag arguments e.g. `--tags foo bar baz`
SIMPLE_TAG_PATTERN = r"^(?P<tag>{})$".format(TAG_VALUE_PATTERN)

# Pattern logic for named tag arguments, e.g. `--tags tag_name=foo,bar,baz`
TAG_VALUES_PATTERN = r"(?P<tags>{pattern}(\,{pattern})*)".format(
    pattern=TAG_VALUE_PATTERN
)
NAMED_TAG_PATTERN = r"^(?P<tag_name>{})={}$".format(
    TAG_NAME_PATTERN, TAG_VALUES_PATTERN
)

# Regexes used for validating & fetching command line arguments
SIMPLE_TAG_REGEX = re.compile(SIMPLE_TAG_PATTERN)
NAMED_TAG_REGEX = re.compile(NAMED_TAG_PATTERN)

# Regexes used for validating tag values & names used in decorators
TAG_VALUE_REGEX = re.compile(r"^{}$".format(TAG_VALUE_PATTERN))
TAG_NAME_REGEX = re.compile(r"^{}$".format(TAG_NAME_PATTERN))

TAG_UNMATCH_TEMPLATE = (
    'Invalid tag {attr_name}: "{{}}", tag {attr_name}s can be any '
    "alphanumeric values, cannot start / end with dash "
    "(`-`), underscore (`_`) or whitespace."
)

TAG_VALUE_UNMATCH_MSG = TAG_UNMATCH_TEMPLATE.format(attr_name="value")
TAG_NAME_UNMATCH_MSG = TAG_UNMATCH_TEMPLATE.format(attr_name="name")


def _validate_string(value, regex, error_msg):
    if not isinstance(value, str):
        raise ValueError(
            "Value {} should be of string type, but it is of type {}".format(
                value, type(value)
            )
        )
    elif not regex.match(value):
        raise ValueError(error_msg.format(value))
    return value


_validate_tag_name_string = functools.partial(  # pylint: disable=invalid-name
    _validate_string, regex=TAG_NAME_REGEX, error_msg=TAG_NAME_UNMATCH_MSG
)

_validate_tag_value_string = functools.partial(  # pylint: disable=invalid-name
    _validate_string, regex=TAG_VALUE_REGEX, error_msg=TAG_VALUE_UNMATCH_MSG
)


def validate_tag_value(tag_value):
    """
    Validate a tag value, make sure it is of correct type.
    Return a tag dict for internal representation.

    Sample input / output:

    'foo' -> {'simple': {'foo'}
    ('foo', 'bar') -> {'simple': {'foo', 'bar'}
    {'color': 'red'} -> {'color': {'red'}
    {'color': ('red', 'blue')} -> {'color': {'red', 'blue'}

    :param tag_value: User defined tag value.
    :type tag_value: ``string``, ``iterable`` of ``string`` or
                     a ``dict`` with ``string`` keys
                     and ``string`` or ``iterable`` of ``string`` as values.

    :return: Internal representation of the tag context.
    :rtype: ``dict`` of ``set``
    """

    def validate_value(value):
        """Make sure tag value is either a string or an iterable of strings."""
        if isinstance(value, str):
            return {_validate_tag_value_string(value)}
        elif isinstance(value, collections.abc.Iterable):
            return {_validate_tag_value_string(tag) for tag in value}
        raise ValueError(
            (
                'Invalid tag value: "{}", only strings, an iterable'
                " of strings or dictionaries are allowed.".format(value)
            )
        )

    if isinstance(tag_value, dict):
        return {
            _validate_tag_name_string(k): validate_value(v)
            for k, v in tag_value.items()
        }
    return {SIMPLE: validate_value(tag_value)}


def merge_tag_dicts(*tag_dicts):
    """Utility function for merging tag dicts for easy comparisons."""
    result = collections.defaultdict(set)
    for tag_dict in tag_dicts:
        for tag_name, tags_set in tag_dict.items():
            result[tag_name] = result[tag_name] | tags_set
    return dict(result)


def tag_label(tag_dict):
    """Return tag data in readable format.

    >>> tag_dict = {
      'simple': set(['foo', 'bar']),
      'tag_group_1': set(['some-value']),
      'other_group': set(['one', 'two', 'three'])
    }

    >>> tag_label(tag_dict)
    Tags: foo bar tag_group_1=some-value other_group=one,two,three
    """

    def format_tags(tag_name, tags):
        """
        Return tags in a format that can be used as --tags argument value.
        """
        tags = sorted(list(tags))
        tags = ["'{}'".format(tag) if " " in tag else tag for tag in tags]

        if tag_name == SIMPLE:
            return " ".join(tags)
        return "{}={}".format(tag_name, ",".join(tags))

    tag_dict = tag_dict.copy()
    tags_list = []
    if SIMPLE in tag_dict:
        tags_list.append((SIMPLE, sorted(tag_dict.pop(SIMPLE))))

    for tag_name in sorted(tag_dict.keys()):
        tags_list.append((tag_name, sorted(tag_dict[tag_name])))

    return " ".join(
        format_tags(tag_name, tags) for tag_name, tags in tags_list
    )


def parse_tag_arguments(*tag_arguments):
    """
    Parse command line tag arguments into a dictionary of sets.

    For the call below:

      ``--tags foo bar named-tag=one,two named-tag=three hello=world``

    We will get:

    .. code-block:: python

      [
        {'simple': {'foo'},
        {'simple', {'bar'},
        {'named_tag', {'one', 'two'},
        {'named_tag', {'three'},
        {'hello', {'world'}
      ]

    The repeated tag values will later on be grouped together via TagsAction.
    """

    def parse_arg(tag_argument):
        simple_match = SIMPLE_TAG_REGEX.match(tag_argument)
        named_match = NAMED_TAG_REGEX.match(tag_argument)

        if simple_match:
            return {SIMPLE: {simple_match.group("tag").strip()}}
        elif named_match:
            tagname = named_match.group("tag_name")
            tags = named_match.group("tags").split(",")
            return {tagname.replace("-", "_"): {tag.strip() for tag in tags}}
        else:
            raise argparse.ArgumentTypeError(
                (
                    'Invalid tag argument: "{}", Please use tag argument '
                    "syntax like:\n\t--tags {}"
                ).format(tag_argument, SAMPLE_ARGUMENTS)
            )

    return merge_tag_dicts(
        *[parse_arg(tag_argument) for tag_argument in tag_arguments]
    )


def check_any_matching_tags(tag_arg_dict, target_tag_dict):
    """Return true if there is at least one match for a category."""
    return any(
        [
            bool(tags_set & target_tag_dict.get(tag_name, set()))
            for tag_name, tags_set in tag_arg_dict.items()
        ]
    )


def check_all_matching_tags(tag_arg_dict, target_tag_dict):
    """
    Return True if all tag sets in `tag_arg_dict` is a subset of the
    matching categories in `target_tag_dict`.
    """
    return all(
        [
            tags_set.issubset(target_tag_dict.get(tag_name, set()))
            for tag_name, tags_set in tag_arg_dict.items()
        ]
    )
