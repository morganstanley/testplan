"""
Parametrization support for test cases.
"""
import collections
import itertools
import re
import warnings

from testplan.common.utils import callable as callable_utils
from testplan.common.utils import convert, interface
from testplan.testing import tagging

# Although any string will be processed as normal, it's a good
# approach to warn the user if the generated method name is not a
# valid python variable name.

# Cannot start with digit, can only contain alphanumerical & underscore
PYTHON_VARIABLE_PATTERN = r"^(?![\d])\w+$"
PYTHON_VARIABLE_REGEX = re.compile(PYTHON_VARIABLE_PATTERN)

# Python attribute names can be of unlimited length but we set a limit here
MAX_METHOD_NAME_LENGTH = 255


class ParametrizationError(ValueError):
    pass


def _check_dict_keys(dictionary, args, required_args):
    dict_keys = set(dictionary.keys())

    missing = set(required_args) - dict_keys
    extra = dict_keys - set(args)

    if missing:
        msg = (
            "The parameter dict keys should at least match the required "
            "argument names, but there were missing keys for the following "
            'arguments: "{}"'.format(",".join(missing))
        )
        raise ParametrizationError(msg)

    if extra:
        msg = (
            "There are extra keys ({extra_keys}) on parameter dict that does "
            'not match any of the testcase arguments: "{arguments}"'.format(
                extra_keys=", ".join(extra), arguments=", ".join(args)
            )
        )
        raise ParametrizationError(msg)

    return dictionary


def _product_of_param_dict(param_dict, args):
    """
    Generate a ``list`` of ``OrderedDict`` using
    the cartesian product of the values in ``param_dict``.

    >>> _product_of_param_dict(
    ...   param_dict={
    ...     'bar': [1, 2],
    ...     'baz': [True, False],
    ...     'foo': ['alpha', 'beta'],
    ...   },
    ...   args=('foo', 'bar', 'baz')
    ... )
    [
      OrderedDict([('foo', 'alpha'), ('bar', 1), ('baz', True)]),
      OrderedDict([('foo', 'alpha'), ('bar', 1), ('baz', False)]),
      OrderedDict([('foo', 'alpha'), ('bar', 2), ('baz', True)]),
      OrderedDict([('foo', 'alpha'), ('bar', 2), ('baz', False)]),
      OrderedDict([('foo', 'beta'), ('bar', 1), ('baz', True)]),
      OrderedDict([('foo', 'beta'), ('bar', 1), ('baz', False)]),
      OrderedDict([('foo', 'beta'), ('bar', 2), ('baz', True)]),
      OrderedDict([('foo', 'beta'), ('bar', 2), ('baz', False)])
    ]
    """
    for val in param_dict.values():
        if not isinstance(val, collections.abc.Iterable) or isinstance(
            val, dict
        ):
            msg = (
                "Dictionary values must be tuple or list of items, {value} "
                "is of type: {type}"
            ).format(value=val, type=type(val))
            raise ParametrizationError(msg)

    keys, values = args, [param_dict[arg] for arg in args]
    product = list(itertools.product(*values))
    return [collections.OrderedDict(zip(keys, vals)) for vals in product]


def _dict_from_arg_tuple(tup, args, required_args, default_args):
    """
    Generate a ``list`` of ``OrderedDict`` using the positional
    values in the ``tup``, mapped as keyword arguments via ``args``.

    >>> _dict_from_arg_tuple(
    ...   tup=(1, 2,),
    ...   args=('foo', 'bar', 'baz'),
    ...   required_args=('foo',),
    ...   default_args={'bar': 10, 'baz': 20}
    ... )
    OrderedDict([('foo', 1), ('bar', 2), ('baz', 20)])
    """
    if len(tup) < len(required_args):
        msg = (
            'Tuple "{arg_tuple}" is missing values '
            'for required arguments: "{required}"'
        )
        raise ParametrizationError(
            msg.format(arg_tuple=tup, required=required_args[len(tup) :])
        )

    elif len(tup) > len(args):
        msg = (
            'Too many values to unpack: Arg tuple: "{arg_tuple}", '
            'function arguments: "{arguments}"'
        )
        raise ParametrizationError(msg.format(arg_tuple=tup, arguments=args))

    ordered_dict = collections.OrderedDict.fromkeys(args)
    kwargs = dict(default_args, **dict(zip(args, tup)))
    ordered_dict.update(kwargs)
    return ordered_dict


def _generate_kwarg_list(parameters, args, required_args, default_args):
    """
    Given the 'raw' parameter context, generate the ``list`` of ``kwargs``
    that will be used for method generation.

    Always returns a list of ``OrderedDict``s regardless of the input type(s).
    """
    # Combinatorial parametrization
    if isinstance(parameters, dict):
        _check_dict_keys(parameters, args, required_args)
        default_args = {k: [v] for k, v in default_args.items()}
        parameters = dict(default_args, **parameters)
        return _product_of_param_dict(parameters, args)

    # Normal parametrization
    elif isinstance(parameters, collections.abc.Iterable):
        dicts = []
        for obj in parameters:

            if not isinstance(obj, (tuple, list, dict)):
                if len(required_args) > 1:
                    raise ParametrizationError(
                        "You can use shortcut notation if and only if the"
                        " testcase has 1 required argument, however"
                        " it has {}".format(len(required_args))
                    )

                obj = convert.make_tuple(obj, convert_none=True)

            if isinstance(obj, (list, tuple)):
                dicts.append(
                    _dict_from_arg_tuple(
                        obj, args, required_args, default_args
                    )
                )

            elif isinstance(obj, dict):
                ordered_dict = collections.OrderedDict.fromkeys(args)
                ordered_dict.update(dict(default_args, **obj))
                dicts.append(
                    _check_dict_keys(ordered_dict, args, required_args)
                )
        return dicts

    msg = (
        '"parameters" should either be a dictionary of iterables with keys '
        "matching method arg names or a list of tuples/lists/dicts that have "
        "corresponding positional/keyword argument values or a list "
        "of non-tuple, non-dict single arguments (shortcut notation)."
        ' Invalid type: {} for "{}"'
    )
    raise ParametrizationError(msg.format(type(parameters), parameters))


def _generate_func(
    function, name, name_func, idx, tag_func, docstring_func, tag_dict, kwargs
):
    """
    Generates a new function using the original function, name generation
    function and parametrized kwargs.

    Also attaches parametrized and explicit tags and apply custom wrappers.
    """

    def _generated(self, env, result):
        return function(self, env, result, **kwargs)

    # If we were given a docstring function, we use it to generate the
    # docstring for each testcase. Otherwise we just copy the docstring from
    # the template method.
    if docstring_func:
        _generated.__doc__ = docstring_func(function.__doc__, kwargs)
    else:
        _generated.__doc__ = function.__doc__

    _generated.__name__ = _parametrization_name_func_wrapper(
        func_name=function.__name__, kwargs=kwargs
    )
    # Users request the feature that when `name_func` set to `None`,
    # then simply append integer suffixes to the names of testcases
    _generated.name = (
        name_func(name, kwargs) if name_func is not None else f"{name} {idx}"
    )

    if hasattr(function, "__xfail__"):
        _generated.__xfail__ = function.__xfail__

    # Tags generated via `tag_func` will be assigned as native tags
    _generated.__tags__ = (
        tagging.validate_tag_value(tag_func(kwargs)) if tag_func else {}
    )

    # Tags index will be merged tag ctx of tag_dict & generated tags
    _generated.__tags_index__ = tagging.merge_tag_dicts(
        _generated.__tags__, tag_dict
    )

    _generated._parametrization_template = function.__name__
    _generated._parametrization_kwargs = kwargs

    return _generated


def _check_name_func(name_func):
    """
    Make sure ``name_func`` is ``None`` or a callable that
    takes ``func_name``, ``kwargs`` arguments.
    """
    if name_func is None:
        return

    if not callable(name_func):
        raise ParametrizationError("name_func must be a callable or `None`")

    try:
        interface.check_signature(name_func, ["func_name", "kwargs"])
    except interface.MethodSignatureMismatch:
        raise ParametrizationError(
            '"name_func" must be a callable that takes 2 arguments'
            ' named "func_name" and "kwargs"'
            " (e.g. def custom_name_func(func_name, kwargs): ..."
        )


def _check_tag_func(tag_func):
    """Make sure ``tag_func`` is a callable that takes ``kwargs`` arguments"""
    if tag_func is None:
        return

    if not callable(tag_func):
        raise ParametrizationError("tag_func must be a callable or `None`")

    try:
        interface.check_signature(tag_func, ["kwargs"])
    except interface.MethodSignatureMismatch:
        raise ParametrizationError(
            'tag_func must be a callable that takes 1 argument named "kwargs"'
            " (e.g. def custom_tag_func(kwargs): ..."
        )


def _parametrization_name_func_wrapper(func_name, kwargs):
    """
    Make sure that name generation doesn't end up with invalid / unreadable
    attribute names/types etc.

    If somehow a 'bad' function name is generated, will just return the
    original ``func_name`` instead (which will later on be suffixed with an
    integer by :py:func:`_ensure_unique_generated_testcase_names`)
    """
    generated_name = parametrization_name_func(func_name, kwargs)

    if not PYTHON_VARIABLE_REGEX.match(generated_name):
        # Generated method name is not a valid Python attribute name.
        # Index suffixed names, e.g. "{func_name}__1", "{func_name}__2", will be used.
        return func_name

    if len(generated_name) > MAX_METHOD_NAME_LENGTH:
        # Generated method name is a bit too long.
        # Index suffixed names, e.g. "{func_name}__1", "{func_name}__2", will be used.
        return func_name

    return generated_name


def parametrization_name_func(func_name, kwargs):
    """
    Method name generator for parametrized testcases.

    >>> import collections
    >>> parametrization_name_func('test_method',
                               collections.OrderedDict(('foo', 5), ('bar', 10)))
    'test_method__foo_5__bar_10'

    :param func_name: Name of the parametrization target function.
    :type func_name: ``str``
    :param kwargs: The order of keys will be the same as the order of arguments
                   in the original function.
    :type kwargs: ``collections.OrderedDict``

    :return: New testcase method name.
    :rtype: ``str``
    """
    arg_strings = ["{arg}_{{{arg}}}".format(arg=arg) for arg in kwargs]
    template = "{func_name}__" + "__".join(arg_strings)
    return template.format(func_name=func_name, **kwargs)


def default_name_func(func_name, kwargs):
    """
    Readable testcase name generator for parametrized testcases.

    >>> import collections
    >>> default_name_func('Test Method',
                          collections.OrderedDict(('foo', 5), ('bar', 10)))
    'Test Method {foo:5, bar:10}'

    :param func_name: Name of the parametrization target function.
    :type func_name: ``str``
    :param kwargs: The order of keys will be the same as the order of arguments
                   in the original function.
    :type kwargs: ``collections.OrderedDict``

    :return: New readable name testcase method.
    :rtype: ``str``
    """
    arg_strings = ["{arg}={{{arg}}}".format(arg=arg) for arg in kwargs]
    template = "{func_name} <" + ", ".join(arg_strings) + ">"
    return template.format(
        func_name=func_name, **{k: repr(v) for k, v in kwargs.items()}
    )


def generate_functions(
    function,
    parameters,
    name,
    name_func,
    tag_dict,
    tag_func,
    docstring_func,
    summarize,
    num_passing,
    num_failing,
    key_combs_limit,
    execution_group,
    timeout,
):
    """
    Generate test cases using the given parameter context, use the name_func
    to generate the name.

    If parameters is of type ``tuple`` / ``list`` then a new testcase method
    will be created for each item.

    If parameters is of type ``dict`` (of ``tuple``/``list``), then a new
    method will be created for each item in the Cartesian product of all
    combinations of values.

    :param function: A testcase method, with extra arguments
                     for parametrization.
    :type function: ``callable``
    :param parameters: Parametrization context for the test case method.
    :type parameters: ``list`` or ``tuple`` of ``dict`` or ``tuple`` / ``list``
                      OR a ``dict`` of ``tuple`` / ``list``.
    :param name: Customized readable name for testcase.
    :type name: ``str``
    :param name_func: Function for generating names of parametrized testcases,
                      should accept ``func_name`` and ``kwargs`` as parameters.
    :type name_func: ``callable``
    :param docstring_func: Function that will generate docstring,
                      should accept ``docstring`` and ``kwargs`` as parameters.
    :type docstring_func: ``callable``
    :param tag_func: Function that will be used for generating tags via
                     parametrization kwargs. Should accept ``kwargs`` as
                     parameter.
    :type tag_func: ``callable``
    :param tag_dict: Tag annotations to be used for each generated testcase.
    :type tag_dict: ``dict`` of ``set``
    :param summarize: Flag for enabling testcase level
                      summarization of all assertions.
    :type summarize: ``bool``
    :param num_passing: Max number of passing assertions
                       for testcase level assertion summary.
    :type num_passing: ``int``
    :param num_failing: Max number of failing assertions
                       for testcase level assertion summary.
    :type num_failing: ``int``
    :param key_combs_limit: Max number of failed key combinations on fix/dict
                            summaries that contain assertion details.
    :type key_combs_limit: ``int``
    :param execution_group: Name of execution group in which the testcases
                            can be executed in parallel.
    :type execution_group: ``str`` or ``NoneType``
    :param timeout: Timeout in seconds to wait for testcase to be finished.
    :type timeout: ``int``
    :return: List of functions that is testcase compliant
             (accepts ``self``, ``env``, ``result`` as arguments) and have
             unique names.
    :rtype: ``list``
    """
    if not parameters:
        raise ParametrizationError('"parameters" cannot be a empty.')

    _check_name_func(name_func)
    _check_tag_func(tag_func)

    argspec = callable_utils.getargspec(function)
    args = argspec.args[3:]  # get rid of self, env, result
    defaults = argspec.defaults or []

    required_args = args[: -len(defaults)] if defaults else args
    default_args = dict(zip(args[len(required_args) :], defaults))

    kwarg_list = _generate_kwarg_list(
        parameters, args, required_args, default_args
    )

    functions = []
    for idx, kwargs in enumerate(kwarg_list):
        func = _generate_func(
            function=function,
            name=name,
            name_func=name_func,
            idx=idx,
            tag_func=tag_func,
            docstring_func=docstring_func,
            tag_dict=tag_dict,
            kwargs=kwargs,
        )
        func.summarize = summarize
        func.summarize_num_passing = num_passing
        func.summarize_num_failing = num_failing
        func.summarize_key_combs_limit = key_combs_limit
        func.execution_group = execution_group
        func.timeout = timeout
        functions.append(func)

    return functions
