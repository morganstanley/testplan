import operator
import inspect
from collections import Mapping, Iterable

import enum
import six

from .exceptions import format_trace
from .reporting import Absent, fmt, NATIVE_TYPES, callable_name


def is_regex(obj):
    """Cannot do type check against SRE_Pattern, so we use duck typing."""
    return hasattr(obj, 'match') and hasattr(obj, 'pattern')


def basic_compare(first, second, strict=False):
    """
        Comparison used for custom match functions,
        can do pattern matching, function evaluation or simple equality.

        Returns traceback if something goes wrong.
    """
    try:
        if is_regex(second):
            if not isinstance(first, six.string_types) and not strict:
                first = str(first)
            result = bool(second.match(first))
        elif callable(second):
            result = bool(second(first))
        else:
            result = first == second
        return result, None
    except Exception as exc:
        return None, format_trace(inspect.trace(), exc)


def is_comparator(value):
    """Utility for finding out a value is a custom comparator or not."""
    return callable(value) or is_regex(value)


def check_dict_keys(data, has_keys=None, absent_keys=None):
    """
        Check if a dictionary contains given
        keys and/or has given keys missing.
    """

    if not (has_keys or absent_keys):
        raise ValueError(
            'Either `has_keys` or `absent_keys` must be provided.')

    keys = set(data.keys())
    has_keys = set(has_keys) if has_keys else set()
    absent_keys = set(absent_keys) if absent_keys else set()

    existing_diff = has_keys - keys
    absent_intersection = absent_keys & keys

    return existing_diff, absent_intersection


class Callable(object):
    """
        Some of our assertions can make use of callables that accept a
        single argument as comparator values. We also provide the helper
        classes below that are composable (via bitwise operators
        or meta callables) and reporting friendly.
    """

    def __call__(self, value):
        raise NotImplementedError

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)

    def __eq__(self, other):
        raise NotImplementedError

    def __invert__(self):
        return Not(self)


class OperatorCallable(Callable):
    """Base class for simple operator based callables."""

    func = None
    func_repr = None

    def __init__(self, reference):
        self.reference = reference

    def __call__(self, value):
        return self.func(value, self.reference)  # pylint: disable=not-callable

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.reference))

    def __eq__(self, other):
        return self.reference == other.reference

    def __str__(self):
        return 'VAL {} {}'.format(self.func_repr, self.reference)


class Less(OperatorCallable):
    func = operator.lt
    func_repr = '<'


class LessEqual(OperatorCallable):
    func = operator.le
    func_repr = '<='


class Greater(OperatorCallable):
    func = operator.gt
    func_repr = '>'


class GreaterEqual(OperatorCallable):
    func = operator.ge
    func_repr = '>='


class Equal(OperatorCallable):
    func = operator.eq
    func_repr = '=='


class NotEqual(OperatorCallable):
    func = operator.ne
    func_repr = '!='


class In(Callable):

    def __init__(self, container):
        self.container = container

    def __call__(self, value):
        return value in self.container

    def __eq__(self, other):
        return self.container == other.container

    def __str__(self):
        return 'VAL in {}'.format(self.container)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.container)


class NotIn(In):

    def __call__(self, value):
        return value not in self.container

    def __str__(self):
        return 'VAL not in {}'.format(self.container)


class IsTrue(Callable):

    def __call__(self, value):
        return bool(value)

    def __str__(self):
        return 'bool(VAL) is True'

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class IsFalse(IsTrue):

    def __call__(self, value):
        return not bool(value)

    def __str__(self):
        return 'bool(VAL) is False'


class MetaCallable(Callable):

    delimiter = None

    def __init__(self, *callables):
        assert [isinstance(clb, Callable) for clb in callables]
        self.callables = callables

    def __eq__(self, other):
        return self.callables == other.callables

    def __repr__(self):
        args = ', '.join(repr(clb) for clb in self.callables)
        return '{}({})'.format(self.__class__.__name__, args)

    def __str__(self):
        delimiter = ' {} '.format(self.delimiter)
        return '({})'.format(
            delimiter.join(str(clb) for clb in self.callables)
        )


class Or(MetaCallable):

    delimiter = 'or'

    def __call__(self, value):
        for clb in self.callables:
            if clb(value):
                return True
        return False


class And(MetaCallable):

    delimiter = 'and'

    def __call__(self, value):
        for clb in self.callables:
            if not clb(value):
                return False
        return True


class Not(Callable):

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, repr(self.callable_obj))

    def __str__(self):
        return 'not ({})'.format(self.callable_obj)

    def __init__(self, callable_obj):
        assert isinstance(callable_obj, Callable)
        self.callable_obj = callable_obj

    def __call__(self, value):
        return not self.callable_obj(value)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
               self.callable_obj == other.callable_obj


class Custom(Callable):
    """
        Utility that allows attaching descriptions to arbitrary functions.

        Useful if you are making use of lambda functions
        and want to provide more context in the reports.

        Usage:
            Custom(
                callable_obj=lambda value: value.custom_method() is True,
                description='`value.custom_method()` returns True'
            )
    """
    def __init__(self, callable_obj, description):
        self.callable_obj = callable_obj
        self.description = description

    def __call__(self, value):
        return self.callable_obj(value)

    def __str__(self):
        return self.description

    def __repr__(self):
        return '{}({}, description={})'.format(
            self.__class__.__name__,
            repr(self.callable_obj),
            self.description
        )

    def __eq__(self, other):
        return all([
            self.__class__ == other.__class__,
            self.callable_obj == other.callable_obj,
            self.description == other.description
        ])


########################################################################
# The non-trivial logic below is used for recursive dict & Fix matching.
# It is not fully compatible with our class based assertion & serialization
# flow, so what we do is generate serializable native data implicitly.
# This may be refactored in future.
########################################################################


# Do not change unless you know what you are doing
# Making this larger will considerably slow down the comparison
MAX_UNORDERED_COMPARE = 16


def compare_with_callable(callable_obj, value):
    try:
        return bool(callable_obj(value)), None
    except Exception as exc:
        return False, format_trace(inspect.trace(), exc)


class RegexAdapter(object):
    """This is being used for internal compatibility."""

    @classmethod
    def check(cls, obj):
        return is_regex(obj)

    @classmethod
    def serialize(cls, obj):
        # TODO: add distinction for flags (e.g. multiline)
        return 0, 'REGEX', obj.pattern

    @classmethod
    def match(cls, regex, value):

        return Match.from_bool(bool(regex.match(value)))

    @staticmethod
    def compare(lhs, rhs):
        """Compare two regular expressions - just do string equality."""
        return Match.from_bool(lhs == rhs)


class Category(object):
    """
    Internal enum. Categorises objects for comparison
    """
    ABSENT = 0
    VALUE = 1
    CALLABLE = 2
    REGEX = 3
    ITERABLE = 4
    DICT = 5


def _categorise(obj, _regex_adapter=RegexAdapter):
    """
    Check type of the object
    """
    if obj is Absent:
        return Category.ABSENT

    obj_t = type(obj)

    if issubclass(obj_t, NATIVE_TYPES):
        return Category.VALUE
    elif callable(obj):
        return Category.CALLABLE
    elif _regex_adapter.check(obj):
        return Category.REGEX
    elif issubclass(obj_t, Mapping):
        return Category.DICT
    elif issubclass(obj_t, Iterable):
        return Category.ITERABLE
    else: # catch-all for types like decimal.Decimal, uuid.UUID, et cetera
        return Category.VALUE


class Match(object):
    """
    Internal enum. Represents the result of a match.
    """
    IGNORED = "i"
    FAIL = "f"
    PASS = "p"

    @staticmethod
    def combine(lhs_match, rhs_match):
        """
        Combines to match levels into a single match level
        """
        lhs_match = lhs_match or Match.IGNORED
        rhs_match = rhs_match or Match.IGNORED
        if lhs_match == Match.IGNORED:
            return rhs_match
        if rhs_match == Match.IGNORED:
            return lhs_match
        if lhs_match == Match.FAIL:
            return Match.FAIL
        if rhs_match == Match.FAIL:
            return Match.FAIL
        return Match.PASS

    @staticmethod
    def from_bool(passed):
        """
        Constructs a match description from a boolean value
        """
        if passed:
            return Match.PASS
        else:
            return Match.FAIL

    @staticmethod
    def to_bool(match):
        """
        Converts a match value to a bool
        """
        if match == Match.FAIL:
            return False
        else: # if (match == Match.PASS) or (match == Match.IGNORED)
            return True


def _build_res(key, match, lhs, rhs):
    """
    Builds a result tuple object for CouchDB.
    """
    return key, match[0], lhs, rhs


def _idictzip_all(lhs_dict, rhs_dict, default=Absent):
    """
    .. warning::

      Internal API.

        Generator that loops through all the keys
        in the left and right hand side dicts.

        Yields key, lhs_val, rhs_val.
        If a key is missing from one of the sides,
        then its value is set to the value of the default
        argument (by default Absent).
    """
    for key, lhs_val in lhs_dict.items():
        yield key, lhs_val, rhs_dict.get(key, default)
    for key, rhs_val in rhs_dict.items():
        if key not in lhs_dict: # if not previously iterated
            yield key, default, rhs_val


def _partition(results):
    """
    .. warning::

      Internal API.

    Splits a list of value results into a two lists of objects for reporting
    """
    lhs_vals = []
    rhs_vals = []
    for result in results:
        key, match, lhs, rhs = result
        if key:
            lhs_vals.append((key, match, lhs))
            rhs_vals.append((key, match, rhs))
        elif match:
            # indicates a list entry containing match information
            lhs_vals.append((3, match, lhs))
            rhs_vals.append((3, match, rhs))
        else:
            lhs_vals.append(lhs)
            rhs_vals.append(rhs)
    return lhs_vals, rhs_vals


def _cmp_dicts(lhs, rhs, ignore, only, report_all, value_cmp_func):
    """
    Compares dictionaries
    """
    def should_ignore_key(key):
        """
            Decide if a key should be ignored.

            Decision is based on ``ignore`` and ``only``.
            If ``only`` is ``True`` then keys that are
             not in ``lhs`` will be ignored.
        """
        if key in ignore:
            should_ignore = True
        elif only is not None:
            should_ignore = key not in only
        else:
            should_ignore = False
        return should_ignore

    results = []
    match = Match.IGNORED
    for iter_key, lhs_val, rhs_val in _idictzip_all(lhs, rhs):
        if should_ignore_key(iter_key):
            if report_all is True:
                results.append(_build_res(
                    key=iter_key,
                    match=Match.IGNORED,
                    lhs=fmt(lhs_val),
                    rhs=fmt(rhs_val)))
        else:
            result = _rec_compare(
                lhs_val,
                rhs_val,
                ignore,
                only,
                iter_key,
                value_cmp_func,
                report_all=report_all)
            results.append(result)
            match = Match.combine(match, result[1])
    return match, results


def _rec_compare(lhs,
                 rhs,
                 ignore,
                 only,
                 key,
                 value_cmp_func,
                 report_all=True,
                 _regex_adapter=RegexAdapter):
    """
    Recursive deep comparison implementation
    """
    # pylint: disable=unidiomatic-typecheck
    lhs_cat = _categorise(lhs)
    rhs_cat = _categorise(rhs)

    ## NO VALS
    if ((lhs_cat == Category.ABSENT) or (rhs_cat == Category.ABSENT)) and \
            (lhs_cat != Category.CALLABLE) and (rhs_cat != Category.CALLABLE):
        return _build_res(
            key=key,
            match=Match.PASS if lhs_cat == rhs_cat else Match.FAIL,
            lhs=fmt(lhs),
            rhs=fmt(rhs))

    ## CALLABLES
    if lhs_cat == rhs_cat == Category.CALLABLE:
        match = Match.from_bool(lhs == rhs)
        return _build_res(
            key=key,
            match=match,
            lhs=(0, 'func', callable_name(lhs)),
            rhs=(0, 'func', callable_name(rhs)))

    if lhs_cat == Category.CALLABLE:
        result, error = compare_with_callable(callable_obj=lhs, value=rhs)
        return _build_res(
            key=key,
            match=Match.from_bool(result),
            lhs=(0, 'func', callable_name(lhs)),
            rhs='Value: {}, Error: {}'.format(
                rhs, error) if error else fmt(rhs))

    if rhs_cat == Category.CALLABLE:
        result, error = compare_with_callable(callable_obj=rhs, value=lhs)
        return _build_res(
            key=key,
            match=Match.from_bool(result),
            lhs='Value: {}, Error: {}'.format(
                lhs, error) if error else fmt(lhs),
            rhs=(0, 'func', callable_name(rhs)))

    ## REGEXES
    if lhs_cat == rhs_cat == Category.REGEX:
        match = _regex_adapter.compare(lhs, rhs)
        return _build_res(
            key=key,
            match=match,
            lhs=_regex_adapter.serialize(lhs),
            rhs=_regex_adapter.serialize(rhs))

    if lhs_cat == Category.REGEX:
        match = _regex_adapter.match(regex=lhs, value=rhs)
        return _build_res(
            key=key,
            match=match,
            lhs=_regex_adapter.serialize(lhs),
            rhs=fmt(rhs))

    if rhs_cat == Category.REGEX:
        match = _regex_adapter.match(regex=rhs, value=lhs)
        return _build_res(
            key=key,
            match=match,
            lhs=fmt(lhs),
            rhs=_regex_adapter.serialize(rhs))

    ## VALUES
    if lhs_cat == rhs_cat == Category.VALUE:
        response = value_cmp_func(lhs, rhs)

        match = Match.from_bool(response)
        return _build_res(
            key=key,
            match=match,
            lhs=fmt(lhs),
            rhs=fmt(rhs))

    ## ITERABLE
    if lhs_cat == rhs_cat == Category.ITERABLE:
        results = []
        match = Match.IGNORED
        for lhs_item, rhs_item in six.moves.zip_longest(lhs, rhs):
            # iterate all elems in both iterable non-mapping objects
            result = _rec_compare(
                lhs_item,
                rhs_item,
                ignore,
                only,
                key=None,
                value_cmp_func=value_cmp_func,
                report_all=report_all)

            match = Match.combine(match, result[1])
            results.append(result)

        # two lists of formatted objects from a
        # list of objects with lhs/rhs attributes
        lhs_vals, rhs_vals = _partition(results)
        return _build_res(
            key=key,
            match=match,
            lhs=(1, lhs_vals),
            rhs=(1, rhs_vals))

    ## DICTS
    if lhs_cat == rhs_cat == Category.DICT:
        match, results = _cmp_dicts(
            lhs, rhs, ignore, only, report_all, value_cmp_func)
        lhs_vals, rhs_vals = _partition(results)
        return _build_res(
            key=key,
            match=match,
            lhs=(2, lhs_vals),
            rhs=(2, rhs_vals))

    ## DIFF TYPES -- catch-all for unhandled
    #  combinations, e.g. VALUE vs ITERABLE
    return _build_res(
        key=key,
        match=Match.FAIL,
        lhs=fmt(lhs),
        rhs=fmt(rhs))


# Built-in functions for comparing values in a dict.
COMPARE_FUNCTIONS = {

    # Compare values in their native types using operator.eq.
    'native_equality': operator.eq,

    # Enforce that object types must be strictly equal before comparing using
    # operator.eq.
    'check_types': lambda x, y: (type(x) == type(y)) and (x == y),

    # Convert all objects to strings using str() before making the comparison.
    'stringify': lambda x, y: str(x) == str(y)
}

def compare(lhs,
            rhs,
            ignore=None,
            only=None,
            report_all=True,
            value_cmp_func=COMPARE_FUNCTIONS['native_equality']):
    """
    Compare two iterable key, value objects (e.g. dict or dict-like mapping)
    and return a status and a detailed comparison table, useful for reporting.

    Ignore has precedence over only.

    :param lhs: object compared against rhs
    :type lhs: ``dict`` interface (``__contains__`` and ``.items()``)
    :param rhs: object compared against lhs
    :type rhs: ``dict`` interface (``__contains__`` and ``.items()``)
    :param ignore: list of keys to ignore in the comparison
    :type ignore: ``list``
    :param only: list of keys to exclusively consider in the comparison
    :type only: ``list``
    :param report_all: include even ignored keys in report
    :type report_all: ``bool`` or ``list``
    :param value_cmp_func: function to compare values in a dict. Defaults
        to COMPARE_FUNCTIONS['native_equality'].
    :type value_cmp_func: Callable[[Any, Any], bool]

    :return: Tuple of comparison bool ``(passed: True, failed: False)`` and
             a description object for the testdb report
    :rtype: ``tuple`` of (``bool``, ``list`` of ``tuple``)
    """

    if (lhs is None) and (rhs is None):
        return (True, [])

    if (lhs is None) or (lhs is Absent):
        return (False, [_build_res(key=entry[0],
                                   match=Match.FAIL,
                                   lhs=fmt(lhs),
                                   rhs=entry[1])
                        for entry in fmt(rhs)[1]])

    if (rhs is None) or (rhs is Absent):
        return (False, [_build_res(key=entry[0],
                                   match=Match.FAIL,
                                   lhs=entry[1],
                                   rhs=fmt(rhs))
                        for entry in fmt(lhs)[1]])

    ignore = ignore or []

    match, comparisons = _cmp_dicts(
        lhs, rhs, ignore, only, report_all, value_cmp_func)

    # In report_all=[key1, key2] case we want to strip out all
    # passed top level keys that are not in this list.
    if not isinstance(report_all, bool):
        for idx, comp in enumerate(comparisons):
            if comp[1] == Match.PASS and comp[0] not in report_all:
                comparisons[idx] = None
        comparisons = [comp for comp in comparisons if comp is not None]

    # For the keys in only not matching anything,
    # we report them as absent in expected and value.
    if isinstance(only, list) and only and comparisons is not None:
        keys_found = set()
        for elem in comparisons:
            keys_found.add(elem[0])
        for key in only:
            if key not in keys_found:
                comparisons.append(
                    (key, Match.IGNORED, Absent.descr, Absent.descr))

    return Match.to_bool(match), comparisons


def _best_permutation(grid):
    """
    Given a square matrix of errors comparing actual
    value vs. expected value, finds the permutation which
    associates actual vs expected with the least error.

    Be careful running this on of large grids, as the
    runtime is expotential O(a^n). Sample run times on desktop hardware::

      size:  0, ms:    0.002  size:  1, ms:    0.010  size:  2, ms:    0.022
      size:  3, ms:    0.046  size:  4, ms:    0.105  size:  5, ms:    0.207
      size:  6, ms:    0.434  size:  7, ms:    0.540  size:  8, ms:    1.351
      size:  9, ms:    2.338  size: 10, ms:    5.470  size: 11, ms:    9.398
      size: 12, ms:   21.651  size: 13, ms:   36.114  size: 14, ms:   79.871
      size: 15, ms:  166.488  size: 16, ms:  363.120  size: 17, ms:  943.494
      size: 18, ms: 1818.761  size: 19, ms: 2370.988  size: 20, ms: 9989.508

    e.g. for the grid::

      >>> grid = [[1000, 2000, 2000],
      ...         [1000, 2000, 2000],
      ...         [   0, 2000, 2000]]
      [1, 2, 0]

    Where [1, 2, 0] is a list of indices mapping::

      - row 0 to col 1
      - row 1 to col 2
      - row 2 to col 0

    """

    def bp_loop(outstanding, level, grid, grid_len, cache):
        """
            Recursively finds a solution by
            progressively excluding poor permutations "paths"
        """
        if not outstanding:
            return 0, []

        # [(cost:int, indx:int)]
        level_permutations = [(grid[level][indx], indx)
                              for indx in outstanding]
        level_permutations.sort()
        min_cost = None
        min_path = None
        for cost, indx in level_permutations:
            remaining = outstanding - frozenset([indx])
            # memoise calls, for large grids
            # this cuts down the amount of calls significantly
            pair = cache.get(remaining, None)
            if pair is None:
                pair = bp_loop(remaining, level + 1, grid, grid_len, cache)
                cache[remaining] = pair
            sub_cost, sub_path = pair
            this_cost = cost + sub_cost
            this_path = [indx] + sub_path
            if (min_cost is None) or (this_cost < min_cost):
                min_cost = this_cost
                min_path = this_path
        return min_cost, min_path

    grid_len = len(grid)

    cache = {}

    # list of int indices
    return bp_loop(frozenset(range(grid_len)), 0, grid, grid_len, cache)[1]


# helper func, used to generate errors matrix
def _to_error(cmpr_tuple, weights):
    """
    Converts a comparison tuple (as returned by compare) to an error.

    Each key may have its own weight. The default weight is 100,
    however this may be otherwise specified in the "weights" dict.
    """
    def is_missed_message(comparisons):
        """
        Returns True if all lhs or rhs values of a dict match are Absent
        """
        absent_side = (0, None, Absent.descr)
        return (
            (
                sum([(0 if entry[2] == absent_side else 1)
                     for entry in comparisons]) == 0
            ) or
            (
                sum([(0 if entry[3] == absent_side else 1)
                     for entry in comparisons]) == 0
            )
        )

    pass_flag, comparisons = cmpr_tuple
    if pass_flag is True:
        return 0 # perfect match
    if pass_flag is False and is_missed_message(comparisons):
        return 100000 # missed message

    # worst possible error: value to normalise against
    worst_error = 0

    current_error = 0
    for comparison in comparisons:
        comparison_match = comparison[1]
        # tag exists and matches, or ignored
        if (comparison_match == Match.PASS) or\
                (comparison_match == Match.IGNORED):
            match_err = 0
        else: # tag exists, but wrong data or tag is missing
            match_err = 1
        tag_weight = weights.get(str(comparison[0]), 100)
        worst_error += tag_weight
        current_error += (match_err * tag_weight)
    return int(current_error * 10000.0 / worst_error + 0.5)


class Expected(object):
    """
    An object representing an expected message,
    along with additional comparison flags.

    Input to the "unordered_compare" function.
    """
    def __init__(self, value, ignore=None, only=None):
        """
        :param value: object compared against
                        each actual value in unordered_compare
        :type value: ``dict``-like interface (__contains__ and .items())
        :param ignore: list of keys to ignore in the comparison
        :type ignore: ``list``
        :param only: list of keys to exclusively consider in the comparison
        :type only: ``list``
        """
        self.value = value
        self.ignore = ignore
        self.only = only


def unordered_compare(
    match_name, values, comparisons, description=None, tag_weightings=None
):
    """
    Matches a list of expected values against a list of expected comparisons.

    The values and comparisons may be specified in
    any order, and the returned value represents the best
    overall match between values and comparisons.

    Initially all value/expected comparison combinations
    are evaluated and converted to an error weight.

    If certain keys/tags are more imporant than others (e.g. ID FIX tags),
    it is possible to give them additional weighting during the comparison,
    by specifying a "tag_weightings" dict.

    The values/comparisons permutation that results in the least
    error is then returned as a list of dicts that can be included
    in the testing report.

    .. note::

      It is possible to specify up to a maximum of
      16 values or expected comparisons.

    .. note::

      ``len(values)`` and ``len(comparison)`` need not be the same.

    :param match_name: name that will appear on comparison report descriptions.
      For example "fixmatch" will produce a comparison description such as
      "unordered fixmatch 2/3: expected[2] vs values[1]"
    :type match_name: ``str``
    :param values: Actual values: an iterable object
                    (e.g. list or generator) of values.
      Each value needs to support a dict-like interface.
    :type values: ``generator`` or ``list`` of ``dict``-like objects
    :param comparisons: Expected values and comparison flags.
    :type comparisons: ``list`` of ``Expected``
    :param description: Message used in each reported match.
    :type description: ``str``
    :param tag_weightings: Per-key overrides that specify a
                            different weight for different keys.
    :type tag_weightings: ``dict`` of ``str`` to ``int``

    :return: A list of test reports that can be appended to the result object
    :rtype: ``list`` of ``dict``
        (keys: 'comparison', 'time', 'description', 'passed', 'objdisplay')
    """
    # make sure that all keys are strings
    weights = {
        str(key): int(val) for key, val in (tag_weightings or {}).items()}

    # input may be generators, we need lists from this point onwards
    list_msgs = list(values)
    list_cmps = list(comparisons)

    # if either the values or expected comparisons
    # exceed 16, then raise an exception:
    # it would take too long to process
    #  (expotential complexity algorithm involved)
    if max(len(list_msgs), len(list_cmps)) > MAX_UNORDERED_COMPARE:
        raise Exception("Too many values being compared. "+
                        "Unordered matching supports up to 16 comparisons")

    # Generate fake comparisons or values in case that the number of values
    # is different from what was expected.
    # This makes it possible to match whatever is possible in the report
    # and mark the rest as either missing or unexpected
    synth_msgs = [Absent] * max(0, len(list_cmps) - len(list_msgs))
    synth_cmps = [Expected(Absent)] * max(0, len(list_msgs) - len(list_cmps))

    # Have to lists of equal sizes to process
    proc_msgs = list_msgs + synth_msgs
    proc_cmps = list_cmps + synth_cmps
    assert len(proc_msgs) == len(proc_cmps)

    # generate a 2D square "matrix" of match (bool pass, list) tuples
    # by calling compare on every message / comparison combination
    # This matrix is organised as:
    #
    #                   # cmp0   cmp1   cmp2   cmp3   # vs:
    #   match_matrix = [[tpl00, tpl01, tpl02, tpl03], # msg0
    #                   [tpl10, tpl11, tpl12, tpl13], # msg1
    #                   [tpl20, tpl21, tpl22, tpl23], # msg2
    #                   [tpl30, tpl31, tpl32, tpl33]] # msg3
    #
    match_matrix = [[compare(cmpr.value,
                             msg,
                             ignore=cmpr.ignore,
                             only=cmpr.only)
                     for cmpr in proc_cmps] for msg in proc_msgs]

    # generate a 2D square "matrix" of error integers (0 <= err <= 1000000)
    # where:
    #   -       0 indicates a perfect message match (no tag mismatches)
    #   -   10000 indicates every tag being wrong between existing messages
    #   - 1000000 indicates a missed or extra
    #               message (when len(msgs) != len(comparisons))
    #
    # Each object in "match_matrix" is mapped to this error int.
    # The shape and position of the matrix is preserved.
    #
    errors_matrix = [[_to_error(cmpr_tuple, weights)
                      for cmpr_tuple in row] for row in match_matrix]

    # compute the optimal matching based on the permutation between actual and
    # expected message that results in the least error
    matched_indices = _best_permutation(errors_matrix)

    # construct a list of report entries
    base_descr = description or "unordered {}".format(match_name)

    def build_descr(msg_indx, cmp_indx, expected_msg, received_msg):
        """
        Build an additional description that indicates
         if the message was missed or unexpected.
        """
        prefix = "{} {}/{}:".format(
            base_descr, msg_indx+1, len(matched_indices))
        if received_msg is Absent:
            return '{} expected[{}] vs Absent'.format(prefix, cmp_indx)
        elif expected_msg is Absent:
            return '{} Absent vs values[{}]'.format(prefix, msg_indx)
        else:
            return '{} expected[{}] vs values[{}]'.format(
                prefix, cmp_indx, msg_indx)

    return [{'description': build_descr(msg_indx,
                                        cmp_indx,
                                        proc_cmps[cmp_indx].value,
                                        proc_msgs[msg_indx]),
             # 'time': now(),  # TODO: use local and UTC times
             'comparison': match_matrix[msg_indx][cmp_indx][1],
             'passed': bool(match_matrix[msg_indx][cmp_indx][0]),
             'comparison_index': cmp_indx}
            for msg_indx, cmp_indx in enumerate(matched_indices)]


def tuplefy_item(item, list_entry=False):
    """
        Convert a dictionary report item in order to
        consume less space in json representation.
    """

    # TODO: Replace magical numbers with constants

    if 'list' in item:
        ret = (1, [tuplefy_item(obj, list_entry=True) for obj in item['list']])
        match = item.get('match')
    elif 'dict' in item:
        ret = (2, [(pair['key'], pair['match'][0], tuplefy_item(pair))
                   if 'match' in pair
                   else (pair['key'], tuplefy_item(pair))
                   for pair in item['dict']])
        match = item.get('match')
    elif 'value' in item:
        if isinstance(item['value'], int):
            ret = (0, item.get('type'), str(item['value']))
        else:
            ret = (0, item.get('type'), item['value'])
        match = item.get('match')
    else:
        raise ValueError('Unmatched type for tuplefy')

    if list_entry and match:
        # list entry that contains match information
        return 3, match[0], ret
    else:
        return ret


def tuplefy_comparisons(comparisons, table=False):
    """
    Convert dictionary report comparisons to list and tuples composition.
    """
    if table:
        return [
            (tuplefy_comparisons(entry['cols']), entry['idx'])
            for entry in comparisons
        ]
    else:
        return [
            (
                comparison['key'],
                comparison['match'][0],
                tuplefy_item(comparison['lhs']),
                tuplefy_item(comparison['rhs'])
            )
            if 'lhs' in comparison and 'rhs' in comparison
            else (comparison['key'], tuplefy_item(comparison['lhs']))
            for comparison in comparisons
        ]


class DictmatchAllResult(object):
    """
    When cast to a ``bool``, evaluates to ``True`` when all values
    were matched without errors or ``False`` if one or more values mis-matched.

    This object exposes two fields:

      - ``passed``: a boolean indicating if the assertion passed completely
      - ``index_match_levels``: a list containing
            tuples of index and match level:

        - ``MATCH``
        - ``MISMATCH``
        - ``LHS_NONE``
        - ``RHS_NONE``

    The following are examples of what the fields
    return under various scenarios:

    .. code-block:: bash

      +-----------------------------------------+--------------------------+
      |    DICTMATCH ASSERTION INPUT            |   DictmatchAllResult     |
      +====================+====================+=========+================+
      | Expected (LHS)     | Actual   (RHS)     | .passed | match levels   |
      +--------------------+--------------------+---------+----------------+
      | [{'id':0,'x':'a'}, | [{'id':0,'x':'a'}, |         | [(0,MATCH),    |
      |  {'id':1,'x':'b'}, |  {'id':2,'x':'c'}, | True    |  (2,MATCH),    |
      |  {'id':2,'x':'c'}] |  {'id':1,'x':'b'}] |         |  (1,MATCH)]    |
      +--------------------+--------------------+---------+----------------+
      | [{'id':0,'x':'a'}, | [{'id':0,'x':'a'}, |         | [(0,MATCH),    |
      |  {'id':1,'x':'b'}, |  {'id':2,'x':'c'}, | False   |  (2,MATCH),    |
      |  {'id':2,'x':'c'}] |  {'id':1}]         |         |  (1,MISMATCH)] |
      +--------------------+--------------------+---------+----------------+
      | [{'id':0,'x':'a'}, | [{'id':0,'x':'a'}, |         | [(0,MATCH),    |
      |  {'id':1,'x':'b'}, |  {'id':3,'x':'d'}, | False   |  (3,LHS_NONE), |
      |  {'id':2,'x':'c'}] |  {'id':1,'x':'b'}, |         |  (1,MATCH),    |
      |                    |  {'id':2,'x':'c'}] |         |  (2,MATCH)]    |
      +--------------------+--------------------+---------+----------------+
      | [{'id':0,'x':'a'}, | [{'id':0,'x':'a'}, |         | [(0,MATCH),    |
      |  {'id':1,'x':'b'}, |  {'id':1,'x':'b'}, | False   |  (1,MATCH),    |
      |  {'id':2,'x':'c'}, |  {'id':3,'x':'d'}] |         |  (3,MATCH),    |
      |  {'id':3,'x':'d'}] |                    |         |  (2,RHS_NONE)] |
      +--------------------+--------------------+---------+----------------+

    Indices are to be read as mappings from RHS values to LHS values.
    i.e.:
        [(1,..),(0,..),(2,..)]
    maps: RHS:0 -> LHS:1, RHS:0 -> LHS:1, RHS:2 -> LHS:2.

    """

    MATCH = 0
    # pylint: disable=W0105
    """
    Perfect match between identified and expected value.
    If all index_match_levels are MATCH, then passed is ``True``.
    """

    MISMATCH = 1
    # pylint: disable=W0105
    """
    The identified and expected values are matched with some errors.
    If any entry in index_match_levels is MISMATCH, then passed is ``False``.
    """

    LHS_NONE = 2
    # pylint: disable=W0105
    """
    A value is present on the right hand side but not matched with
    a value on the left hand side. (e.g. an unexpected message).
    If any entry in index_match_levels is LHS_NONE, then passed is ``False``.
    """

    RHS_NONE = 3
    # pylint: disable=W0105
    """
    A value is present on the left hand side but not matched with
    a value on the right hand side. (e.g. a missed message)
    If any entry in index_match_levels is RHS_NONE, then passed is ``False``.
    """

    def __init__(self, passed, index_match_levels):
        """
        Constructs a new DictmatchAllResult object.
        :param passed: Set to True if the assertion passed on
                        all its inputs, False otherwise
        :type passed: ``bool``
        :param index_match_levels: A list of mappings between
                                    matched index and level of matching.
        :type index_match_levels: ``list`` of
            (``int``, ``MATCH``, ``MISMATCH``, ``LHS_NONE`` or ``RHS_NONE``)
            tuples.
        """
        self.passed = passed
        self.index_match_levels = index_match_levels

    def __bool__(self): # python 3 bool()
        """
        :return: True if assertion passed, False otherwise
        :rtype: ``bool``
        """
        return self.passed

    def __nonzero__(self): # python 2 bool()
        """
        :return: True if assertion passed, False otherwise
        :rtype: ``bool``
        """
        return self.passed


def dictmatch_all_compat(
    match_name, comparisons, values,
    description, key_weightings,
):
    """This is being used for internal compatibility."""
    matches = unordered_compare(
        match_name=match_name,
        values=values,
        comparisons=comparisons,
        description=description,
        tag_weightings=key_weightings
    )

    all_passed = True
    indices = []
    levels = []

    for mtch in matches:
        # mtch['is_fix'] = is_fix
        passed = mtch['passed']
        cmp_indx = mtch['comparison_index']
        indices.append(cmp_indx)
        if passed:
            level = DictmatchAllResult.MATCH
        elif (cmp_indx < len(comparisons)) and (cmp_indx < len(values)):
            level = DictmatchAllResult.MISMATCH
        # (implicit) : and (cmp_indx >= len(values))
        elif cmp_indx < len(comparisons):
            level = DictmatchAllResult.RHS_NONE
        # cmp_indx < len(values) and (cmp_indx >= len())
        else:
            level = DictmatchAllResult.LHS_NONE

        levels.append(level)

        if not passed:
            all_passed = False

    res = DictmatchAllResult(all_passed, zip(indices, levels))
    return matches, res
