"""TODO."""

import re
import six
import argparse
import warnings
import functools
import collections


SAMPLE_ARGUMENTS = """tag1 tag2 tagname1=tag3,tag4 tagname2=tag5,tag6"""

SIMPLE = 'simple'  # key for simple tags

# Both tag values and tag names cannot start & end with dash / underscore
# (for readable URL params)

# Currently allowing same patterns for tags and tag names
TAG_VALUE_PATTERN = r"(?![\s\_-])[\w\s-]+(?<![\s\_-])"
TAG_NAME_PATTERN = TAG_VALUE_PATTERN

# Pattern for simple tag arguments e.g. `--tags foo bar baz`
SIMPLE_TAG_PATTERN = r'^(?P<tag>{})$'.format(TAG_VALUE_PATTERN)

# Pattern logic for named tag arguments, e.g. `--tags tag_name=foo,bar,baz`
TAG_VALUES_PATTERN = r'(?P<tags>{pattern}(\,{pattern})*)'.format(
    pattern=TAG_VALUE_PATTERN)
NAMED_TAG_PATTERN = r'^(?P<tag_name>{})={}$'.format(
    TAG_NAME_PATTERN, TAG_VALUES_PATTERN)

# Regexes used for validating & fetching command line arguments
SIMPLE_TAG_REGEX = re.compile(SIMPLE_TAG_PATTERN)
NAMED_TAG_REGEX = re.compile(NAMED_TAG_PATTERN)

# Regexes used for validating tag values & names used in decorators
TAG_VALUE_REGEX = re.compile(r'^{}$'.format(TAG_VALUE_PATTERN))
TAG_NAME_REGEX = re.compile(r'^{}$'.format(TAG_NAME_PATTERN))

TAG_UNMATCH_TEMPLATE = (
    'Invalid tag {attr_name}: "{{}}", tag {attr_name}s can be any '
    'alphanumeric values, cannot start / end with dash '
    '(`-`), underscore (`_`) or whitespace.')

TAG_VALUE_UNMATCH_MSG = TAG_UNMATCH_TEMPLATE.format(attr_name='value')
TAG_NAME_UNMATCH_MSG = TAG_UNMATCH_TEMPLATE.format(attr_name='name')


def _prevent_tag_reassignment(obj, attr_name):
    if hasattr(obj, attr_name):
        raise AttributeError('{} already has tags set.'.format(obj))


def _validate_string(value, regex, error_msg):
    if not isinstance(value, six.string_types):
        raise ValueError(
            'Value {} should be of string type, but it is of type {}'.format(
                value, type(value)))
    elif not regex.match(value):
        raise ValueError(error_msg.format(value))
    return value


_validate_tag_name_string = functools.partial(  # pylint: disable=invalid-name
    _validate_string, regex=TAG_NAME_REGEX, error_msg=TAG_NAME_UNMATCH_MSG)

_validate_tag_value_string = functools.partial(  # pylint: disable=invalid-name
    _validate_string, regex=TAG_VALUE_REGEX, error_msg=TAG_VALUE_UNMATCH_MSG)


def validate_tag_value(tag_value):
    """
    Validate a tag value, make sure it is of correct type.
    Return a tag dict for internal representation.

    :param tag_value: User defined tag value.
    :type tag_value: ``string``, ``iterable`` of ``string`` or
                     a ``dict`` with ``string`` keys
                     and ``string`` or ``iterable`` of ``strings`` as values.

    :return: Internal representation of the tag context.
    :rtype: ``dict`` of ``frozenset``
    """
    def validate_value(value):
        """Make sure tag value is either a string or an iterable of strings."""
        if isinstance(value, six.string_types):
            return frozenset([_validate_tag_value_string(value)])
        elif isinstance(value, collections.Iterable):
            return frozenset([_validate_tag_value_string(tag) for tag in value])
        raise ValueError((
            'Invalid tag value: "{}", only strings, an iterable'
            ' of strings or dictionaries are allowed.'.format(value)))

    if isinstance(tag_value, dict):
        return {_validate_tag_name_string(k): validate_value(v)
                for k, v in tag_value.items()}
    return {SIMPLE: validate_value(tag_value)}


def merge_tag_dicts(*tag_dicts):
    """Utility function for merging tag dicts for easy comparisons."""
    result = collections.defaultdict(frozenset)
    for tag_dict in tag_dicts:
        for tag_name, tags_set in tag_dict.items():
            result[tag_name] = result[tag_name] | tags_set
    return dict(result)


def get_native_testcase_tags(test_case):
    """Return tags that are explicitly assigned to a test case method."""
    return getattr(test_case, 'tags', {})


def get_native_suite_tags(suite):
    """Return tags that are explicitly assigned to a suite."""
    return getattr(suite, '__TAGS__', {})


def get_native_test_tags(test):
    """Return tags that are explicitly assigned to a test."""
    # Test instances don't have native tag support yet
    # When we add support for this, get_test_tags,
    # get_testcase_tags and get_suite_tags should also change.
    return getattr(test, 'tags', {})


def get_testcase_tags(test_case):
    """A suite's tag also apply to a test case method."""
    suite = test_case.im_class if six.PY2 else test_case.__self__.__class__
    return merge_tag_dicts(
        get_native_suite_tags(suite),
        get_native_testcase_tags(test_case))


def get_suite_tags(suite):
    """Get all tag data from a suite, including merged testcase tags."""
    tag_dicts = [get_native_suite_tags(suite)]
    if hasattr(suite, 'get_testcase_methods'):
        tag_dicts.extend([method.tags
                          for _, method in suite.get_testcase_methods().items()
                          if hasattr(method, 'tags')])
    return merge_tag_dicts(*tag_dicts)


def get_test_tags(test):
    """Get all tag data from a test, including merged suite tags."""
    # Currently only MultiTest has support for tag filtering

    from testplan.testing.multitest import MultiTest
    if not isinstance(test, MultiTest):
        return {}

    return merge_tag_dicts(*[get_suite_tags(suite) for suite in test.suites])


def _check_duplicate_tag_names(suite):
    """
    Display warning if suite level tags are duplicates of method level
    tags and vice versa.
    """

    suite_level_tags = get_native_testcase_tags(suite)
    if suite_level_tags and hasattr(suite, 'get_testcase_methods'):
        for tname, tmethod in suite.get_testcase_methods().items():
            if hasattr(tmethod, 'tags'):
                intersects = {
                    tag_name: tags & tmethod.tags.get(tag_name, frozenset())
                    for tag_name, tags in suite_level_tags.items()
                    }
                duplicates = {k: v for k, v in intersects.items() if v}

                for tag_name, dupes in duplicates.items():
                    tag_template = '{dupes}'\
                        if tag_name == SIMPLE else '{tag_name} = {dupes}'
                    msg = ('Duplicate tags found, Suite: {testsuite},'
                           ' Method: {testsuite}.{method_name}, Tags: "%s".'
                           ' Re-assigning suite level tags to testcases is a '
                           'redundant operation.' % tag_template)
                    msg = msg.format(
                        tag_name=tag_name, dupes=', '.join(dupes),
                        testsuite=suite.__name__, method_name=tname)
                    warnings.warn(msg)


def _check_duplicate_tag_values(tag_target, tag_dict):
    """
    Display warning if the user assigns same tag value for
    different groups (which may cause confusion).

    e.g. @testcase(tags={tag_name_1='foo', tag_name_2='foo'})
    """
    tag_dict_reversed = collections.defaultdict(set)
    for tag_name, tag_values in tag_dict.items():
        for value in tag_values:
            tag_dict_reversed[value].add(tag_name)

    dupes = {
        tag_value: tag_names
        for tag_value, tag_names in tag_dict_reversed.items()
        if len(tag_names) > 1
        }

    for tag_value, tag_names in dupes.items():
        msg = (
            '{tag_target}: Duplicate tag value ("{tag_value}") is being used '
            'for different tag names ("{tag_names}").'
        ).format(
            tag_target=tag_target,
            tag_value=tag_value,
            tag_names=', '.join(tag_names))
        warnings.warn(msg)


def attach_testcase_tags(test_case, tag_value):
    """Assign a tag dict to a method."""
    tag_dict = validate_tag_value(tag_value)
    _prevent_tag_reassignment(test_case, 'tags')
    _check_duplicate_tag_values(test_case, tag_dict)
    test_case.tags = tag_dict
    return test_case


def attach_suite_tags(suite, tag_value):
    """
    Assign a tag dict to a testsuite class, display warnings
    if testsuite level tags match method level tags.
    """
    tag_dict = validate_tag_value(tag_value)
    _prevent_tag_reassignment(suite, '__TAGS__')
    suite.__TAGS__ = tag_dict

    _check_duplicate_tag_values(suite, tag_dict)
    _check_duplicate_tag_names(suite)
    return suite


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
        tags = ["'{}'".format(tag) if ' ' in tag else tag for tag in tags]

        if tag_name == SIMPLE:
            return ' '.join(tags)
        return '{}={}'.format(tag_name, ','.join(tags))

    tag_dict = tag_dict.copy()
    tags_list = []
    if SIMPLE in tag_dict:
        tags_list.append((SIMPLE, sorted(tag_dict.pop(SIMPLE))))

    for tag_name in sorted(tag_dict.keys()):
        tags_list.append((tag_name, sorted(tag_dict[tag_name])))

    return ' '.join(format_tags(tag_name, tags) for tag_name, tags in tags_list)


def parse_tag_arguments(*tag_arguments):
    """
    Parse command line tag arguments into a dictionary of frozensets.

    For the call below:

      ``--tags foo bar named-tag=one,two named-tag=three hello=world``

    We will get:

    .. code-block:: python

      [
        {'simple': frozenset(['foo'])},
        {'simple', frozenset(['bar'])},
        {'named_tag', frozenset(['one', 'two'])},
        {'named_tag', frozenset(['three'])},
        {'hello', frozenset(['world'])}
      ]

    The repeated tag values will later on be grouped together via TagsAction.
    """
    def parse_arg(tag_argument):
        simple_match = SIMPLE_TAG_REGEX.match(tag_argument)
        named_match = NAMED_TAG_REGEX.match(tag_argument)

        if simple_match:
            return {SIMPLE: frozenset([simple_match.group('tag').strip()])}
        elif named_match:
            tagname = named_match.group('tag_name')
            tags = named_match.group('tags').split(',')
            return {tagname.replace('-', '_'): frozenset([tag.strip()
                                                          for tag in tags])}
        else:
            raise argparse.ArgumentTypeError(
                ('Invalid tag argument: "{}", Please use tag argument '
                 'syntax like:\n\t--tags {}').format(
                    tag_argument, SAMPLE_ARGUMENTS))
    return merge_tag_dicts(
        *[parse_arg(tag_argument) for tag_argument in tag_arguments])


def check_any_matching_tags(tag_arg_dict, target_tag_dict):
    """Return true if there is at least one match for a category."""
    return any([bool(tags_set & target_tag_dict.get(tag_name, frozenset()))
                for tag_name, tags_set in tag_arg_dict.items()])


def check_all_matching_tags(tag_arg_dict, target_tag_dict):
    """
    Return True if all tag sets in `tag_arg_dict` is a subset of the
    matching categories in `target_tag_dict`.
    """
    return all([tags_set.issubset(target_tag_dict.get(tag_name, frozenset()))
                for tag_name, tags_set in tag_arg_dict.items()])


def _matcher(tag_getter, tag_arg_dict, match_func):
    """Match function builder"""
    def _match(obj):
        return match_func(
            target_tag_dict=tag_getter(obj),
            tag_arg_dict=tag_arg_dict)
    return _match


class TagsAction(argparse.Action):
    """
    Returns 3 filter functions:
      - test filter -> Applied at test class level (e.g. ``MultiTest``)
      - suite filter -> Applied to a suite class
                       (e.g. decorated with ``@testsuite``)
      - testcase filter -> Applied to a testcase method of a suite
                          (e.g. decorated with ``@testcase``)

    A test will run only if all filter functions return True for their target.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # Merge tag values for the same tag names
        matcher = functools.partial(
            _matcher,
            tag_arg_dict=merge_tag_dicts(*values),
            match_func=self._get_match_function())

        test_matcher = matcher(tag_getter=get_test_tags)
        suite_matcher = matcher(tag_getter=get_suite_tags)
        testcase_matcher = matcher(tag_getter=get_testcase_tags)

        values = (test_matcher, suite_matcher, testcase_matcher)
        setattr(namespace, self.dest, values)

    def _get_match_function(self):  # pylint: disable=no-self-use
        return check_any_matching_tags


class TagsAllAction(TagsAction):
    """
    Similar to TagsAction, however ALL tags should match
    instead of at least one.
    """

    def _get_match_function(self):  # pylint: disable=no-self-use
        return check_all_matching_tags


class TempTagsAction(argparse.Action):
    """Temporary replacement for TagsAction & TagsAllAction"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, merge_tag_dicts(*values))
