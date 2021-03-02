"""Conversion utilities."""
import itertools

from .reporting import Absent


def make_tuple(value, convert_none=False):
    """Shortcut utility for converting a value to a tuple."""
    if isinstance(value, list):
        return tuple(value)
    if not isinstance(value, tuple) and (convert_none or value is not None):
        return (value,)
    return value


def sort_and_group(iterable, key):
    """Sort an iterable and group the items by the given key func"""
    groups = [
        (k, list(g))
        for k, g in itertools.groupby(sorted(iterable, key=key), key=key)
    ]
    return groups


def nested_groups(iterable, key_funcs):
    """
    Create nested groups from the given ``iterable`` using ``key_funcs``

    Key functions will be applied for sorting and group, beginning from the
    first function (top level).

    The sample below will give us 2 top level groups and 4 sub groups:

        * Numbers divisible by 10

            - Numbers divisible by 10 and divisible by 3
            - Numbers divisible by 10 and not divisible by 3

        * Numbers not divisible by 10

            - Numbers not divisible by 10 and divisible by 3
            - Numbers not divisible by 10 and not divisible by 3

    >>> nested_groups(
    ...    range(1, 100),
    ...    key_funcs=[
    ...        lambda obj: obj % 10 == 0,
    ...        lambda obj: obj % 3 == 0
    ...    ]
    ... )

    """
    first, rest = key_funcs[0], key_funcs[1:]
    grouping = sort_and_group(iterable, first)
    if rest:
        return [(key, nested_groups(group, rest)) for key, group in grouping]
    else:
        return grouping


def make_iterables(values):
    """
    Create a list of iterables (``list`` and ``tuple``) containing each of the
    values passed as a parameter. It was designed to be used when defining types
    in the configuration schema. For example make_iterables([str, ContextVale])
    will return  [[str], (str,), [ContextValue], (ContextValue,)].

    :param values: List of values to place in each iterable.
    :type values: ``list``

    :return: List of iterables containing one of each of the values.
    :rtype: ``list`` of ``list`` and ``tuple``
    """
    iterables = []
    for value in values:
        iterables.append([value])
        iterables.append((value,))
    return iterables


def full_status(status):
    """Human readable status label."""
    if status == "p":
        return "Passed"
    elif status == "f":
        return "Failed"
    elif status == "i":
        return "Ignored"
    return ""


def expand_values(rows, level=0, ignore_key=False, key_path=None):
    """
    Recursively yield all rows of VAL items (key, match, VAL).
    """
    if key_path is None:
        key_path = []

    for row in rows:
        # While comparing dict value (list type), dict key is ignored, thus
        # a special object `Absent` is used as key, which means no key here.
        key = row[0] if ignore_key is False else Absent
        if key is not Absent:  # `None` or empty string can also be used as key
            key_path.append(key)

        match = row[1] if len(row) == 3 else ""
        val = row[2] if len(row) == 3 else row[1]

        if isinstance(val, tuple):
            if val[0] == 0:  # value
                yield (tuple(key_path), level, key, match, (val[1], val[2]))
            elif val[0] in (1, 2, 3):
                yield (tuple(key_path), level, key, match, "")
                for new_row in expand_values(
                    val[1],
                    level=level + 1,
                    ignore_key=True if val[0] == 1 else False,
                    key_path=key_path,
                ):
                    yield new_row
        elif isinstance(val, list):
            yield (tuple(key_path), level, key, match, "")
            for new_row in expand_values(val, level=level, key_path=key_path):
                yield new_row

        if key is not Absent:
            key_path.pop()


def extract_values(comparison, position):
    """
    Create list of (key, match, val) from
    top level [(key, value, VAL, VAL)] structure.
    """
    result = []
    for item in comparison:
        result.append((item[0], item[1], item[position]))
    return result


def flatten_formatted_object(formatted_obj):
    """
    Flatten the formatted object which is the result of function
    ``testplan.common.utils.reporting.fmt``.

    :param formatted_obj: The formatted object

    :return: List representation of flattened object
    :rtype: ``list``
    """

    def flatten(obj, level=0, ignore_key=True):
        if ignore_key:
            key = ""
        else:
            key, obj = obj[0], obj[1]

        if isinstance(obj, tuple):
            if obj[0] == 0:
                yield (level, key, (obj[1], obj[2]))
            elif obj[0] in (1, 2):
                yield (level, key, "")
                for row in obj[1]:
                    for new_row in flatten(
                        row, level=level + 1, ignore_key=(obj[0] == 1)
                    ):
                        yield new_row
            else:
                raise ValueError("Invalid data found in formatted object")
        else:
            raise ValueError("Invalid data found in formatted object")

    if formatted_obj[0] == 0:
        return list(flatten(formatted_obj))
    else:
        result_table = []
        for level, key, val in flatten(formatted_obj, level=-1):
            result_table.append([level, key, val])

        if formatted_obj[0] == 2:
            for idx in range(1, len(result_table)):
                if not result_table[idx][1]:  # no key
                    result_table[idx][0] -= 1

        while True:
            level_decreased = False
            prev_level = 0
            for idx in range(1, len(result_table)):
                level = result_table[idx][0]
                if level > prev_level + 1:
                    for inner_idx in range(idx, len(result_table)):
                        if result_table[inner_idx][0] > prev_level:
                            level_decreased = True
                            result_table[inner_idx][0] -= 1
                        else:
                            break
                prev_level = level
            if level_decreased is False:
                break

        return result_table[1:]


def flatten_dict_comparison(comparison):
    """
    Flatten the comparison object from dict/fix match into a list of rows.

    Row elements: [level, key, status, left, right]

    i.e:

    .. code-block:: python

      [
          [0, 555, 'Passed', '', ''],
          [0, '', 'Passed', '', ''],                       # Group result
          [2, 600, 'Passed', ('str', 'A'), ('str', 'A')],
          [2, 601, 'Passed', ('str', 'A'), ('str', 'A')],
          [2, 683, 'Passed', '', ''],
          [2, '', 'Passed', '', ''],                       # Group result
          [4, 688, 'Passed', ('str', 'a'), ('str', 'a')],
          [4, 689, 'Passed', ('str', 'a'), ('str', 'a')],
          [2, '', 'Passed', '', ''],                       # Group result
          [4, 688, 'Passed', ('str', 'b'), ('str', 'b')],
          [4, 689, 'Passed', ('str', 'b'), ('str', 'b')]
      ]
    """
    result_table = []  # level, key, left, right, result

    left = list(expand_values(extract_values(comparison, 2)))
    right = list(expand_values(extract_values(comparison, 3)))

    while left or right:
        lpart, rpart = None, None
        if left and right:
            if len(left[0][0]) > len(right[0][0]):
                lpart = left.pop(0)
            elif len(left[0][0]) < len(right[0][0]):
                rpart = right.pop(0)
            else:
                lpart, rpart = left.pop(0), right.pop(0)
        elif left:
            lpart = left.pop(0)
        elif right:
            rpart = right.pop(0)

        level = lpart[1] if lpart else rpart[1]
        key = lpart[2] if lpart else rpart[2]
        if key is Absent:
            level -= 1
            # key = '(group)'

        status = full_status(lpart[3] if lpart else rpart[3])
        lval = lpart[4] if lpart else None
        rval = rpart[4] if rpart else None
        result_table.append(
            [level, "" if key is Absent else key, status, lval, rval]
        )

    while True:
        level_decreased = False
        prev_level = 0
        for idx in range(len(result_table)):
            level = result_table[idx][0]
            if level > prev_level + 1:
                for inner_idx in range(idx, len(result_table)):
                    if result_table[inner_idx][0] > prev_level:
                        level_decreased = True
                        result_table[inner_idx][0] -= 1
                    else:
                        break
            prev_level = level
        if level_decreased is False:
            break

    return result_table
