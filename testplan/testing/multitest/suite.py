"""Multitest testsuite/testcase module."""
import collections
import copy
import dataclasses
import functools
import inspect
import itertools
import types
import warnings
from typing import Callable, Optional

from testplan import defaults
from testplan.common.utils import interface, strings
from testplan.testing import tagging

from . import parametrization
from .test_metadata import (
    LocationMetadata,
    TestCaseMetadata,
    TestCaseStaticMetadata,
    TestSuiteMetadata,
    TestSuiteStaticMetadata,
)

# Global variables
__TESTCASES__ = []
__PARAMETRIZATION_TEMPLATE__ = []
__GENERATED_TESTCASES__ = []


TESTCASE_METADATA_ATTRIBUTE = "__testcase_metadata__"
TESTSUITE_METADATA_ATTRIBUTE = "__testsuite_metadata__"


def _reset_globals():
    # pylint: disable=global-statement
    global __TESTCASES__
    global __PARAMETRIZATION_TEMPLATE__
    global __GENERATED_TESTCASES__

    __TESTCASES__ = []
    __PARAMETRIZATION_TEMPLATE__ = []
    __GENERATED_TESTCASES__ = []


def update_tag_index(obj, tag_dict):
    """
    Utility for updating ``__tags_index__`` attribute of an object.
    """
    if isinstance(obj, types.MethodType):
        obj = obj.__func__

    obj.__tags_index__ = tagging.merge_tag_dicts(
        tag_dict, getattr(obj, "__tags_index__", {})
    )


def propagate_tag_indices(suite, tag_dict):
    """
    Update tag indices of the suite instance / class and its children (e.g.
    testcases, parametrization templates).

    For multitest we support multiple levels of tagging:

      1. Multitest (top) level
      2. Suite level
      3. Testcase / parametrization level

    When a test suite class is defined, the native tags of
    the suite is used for updating test indices of
    unbound testcase methods and vice versa. These
    test indices are shared among all instances of
    this suite.

    Later on when an instance of the suite class
    is initialized and added to a multitest, test
    indices of the suite object and its bound testcase
    methods are updated multitest object's native tags.

    This means different instances of the same suite
    class may end up having different tag indices if they
    are added to different multitests that have different native tags.

    E.g. when we have a suite & testcases with native tags like:

    .. code-block:: text

      MySuite -> {'color': 'red'}
          testcase_one -> no tags
          testcase_two -> {'color': 'blue', 'speed': 'fast'}
          parametrized_testcase -> {'color': 'yellow'}
              generated_testcase_1 -> no tags
              generated_testcase_2 -> no tags

    We will have the following tag indices:

    .. code-block:: text

      MySuite -> {'color': {'red', 'blue', 'yellow'}, 'speed': {'fast'}}
          testcase_one -> {'color': 'red'}
          testcase_two -> {'color': {'blue', 'red'}, 'speed': 'fast'}
          parametrized_testcase -> NO TAG INDEX
              generated_testcase_1 -> {'color': {'yellow', 'red'}}
              generated_testcase_2 -> {'color': {'yellow', 'red'}}

    Parametrization method templates do not have tag index attribute, as
    they are not run as tests and their tags are propagated to generated
    testcases (and eventually up to the suite index).
    """
    update_tag_index(suite, tag_dict)

    for child in get_testcase_methods(suite):
        update_tag_index(child, tag_dict)


def get_testsuite_name(suite):
    """
    Returns the name to be used for the given testsuite. This is made of
    either the class name or the result of `name` (can be a normal string
    or a function returning a string) if it exists. The first time this
    function is called the suite name will be saved for future use.

    :param suite: Suite object whose name is needed
    :type suite: ``testsuite``

    :return: Name of given suite
    :rtype: ``str``
    """
    if "name" not in suite.__dict__:
        if suite.__class__.name is None:
            suite.name = suite.__class__.__name__
        elif isinstance(suite.__class__.name, str):
            suite.name = suite.__class__.name
        elif callable(suite.__class__.name):
            suite.name = suite.name.__func__(suite.__class__.__name__, suite)
        else:  # Should not go here, argument already verified in `_testsuite`
            raise RuntimeError('Invalid argument "name" in "{}"'.format(suite))

    if not isinstance(suite.name, str):
        raise ValueError(
            'Test suite name "{name}" must be a string, it is of type:'
            " {type}".format(name=suite.name, type=type(suite.name))
        )
    elif not suite.name:
        raise ValueError("Test suite name cannot be an empty string")

    if len(suite.name) > defaults.MAX_TEST_NAME_LENGTH:
        warnings.warn(
            'Name defined for test suite "{}" is too long,'
            ' consider customizing test suite name with argument "name"'
            " in @testsuite decorator.".format(suite.__class__.__name__)
        )

    if ":" in suite.name:
        warnings.warn(
            "Test suite object contains colon in name: {}".format(suite.name)
        )

    import types

    suite.uid = types.MethodType(lambda self: self.name, suite)
    return suite.name


def get_testsuite_desc(suite):
    """
    Return the description of the testsuite.

    Remove trailing line returns if applicable, they look nasty
    in the reports (text and otherwise)
    """
    desc = suite.__doc__
    return strings.format_description(desc.rstrip()) if desc else None


def set_testsuite_testcases(suite):
    """
    Build the list of testcases to run for the given testsuite. The name of
    each testcase should be unique.

    :param suite: Suite object whose testcases need to be set
    :type suite: ``testsuite``

    :return: ``None``
    :rtype: ``NoneType``
    """
    testcases = []
    testcase_names = set()

    for testcase in suite.__class__.__testcases__:
        if not hasattr(suite, testcase):
            raise AttributeError(
                "{} does not have a testcase method named: {}".format(
                    suite, testcase
                )
            )

        testcase_method = getattr(suite, testcase)
        if testcase_method.name in testcase_names:
            raise ValueError(
                "Duplicate testcase name {} found, please check."
                ' Or use "name_func" argument to generate names for'
                " parametrized testcases.".format(testcase_method.name)
            )

        skip_reason: Optional[str] = None
        for skip_func in testcase_method.__skip__:
            if skip_func(suite):
                skip_reason = (
                    f'File "{inspect.getsourcefile(skip_func)}",\n'
                    f"line {inspect.getsourcelines(skip_func)[1]},\n"
                    f"{skip_func.__qualname__} evaluated to true, "
                    "skipping execution"
                )
                break

        if skip_reason:
            # replace the original testcase with testcase holding result.skip
            setattr(
                suite,
                testcase,
                _gen_skipped_case(skip_reason, testcase_method),
            )
            testcases.append(testcase)
            testcase_names.add(testcase_method.name)
        else:
            testcases.append(testcase)
            testcase_names.add(testcase_method.name)

    setattr(suite, "__testcases__", testcases)


def _gen_skipped_case(skip_reason, orig_case):
    """
    Generate a new testcase with body replaced by "result.skip".
    """

    def _f(_, result):
        result.skip(skip_reason)

    # since the original name has been already validated
    _f.name = orig_case.name
    _f.__name__ = orig_case.__name__
    _f.__doc__ = orig_case.__doc__
    _f.__tags__ = orig_case.__tags__
    _f.__tags_index__ = orig_case.__tags_index__
    _f.__should_skip__ = True
    # NOTE: interactive reloader will regenerate the skipped testcase
    #             so it will need the __skip__ attribute.
    _f.__skip__ = orig_case.__skip__
    _mark_function_as_testcase(_f)
    return _f


def get_testcase_desc(suite, testcase_name):
    """
    Return the description of the testcase with the given name of the
    given testsuite.

    Remove trailing line returns if applicable, they look nasty
    in the reports (text and otherwise)
    """
    desc = getattr(suite, testcase_name).__doc__
    return strings.format_description(desc.rstrip()) if desc else ""


def get_testcase_methods(suite):
    """
    Return the unbound method objects marked as a testcase
    from a testsuite class.
    """
    return [
        getattr(suite, testcase_name)
        for testcase_name in suite.__testcases__
        if callable(getattr(suite, testcase_name))
    ]


def _selective_call(decorator_func, meta_func, wrapper_func):
    """
    This hacky higher order function gives us the flexibility of using the
    'same' decorator with or without extra arguments. So both declarations will
    be valid:

    .. code-block:: python

      class Foo:

        @some_decorator
        def method_1(self):
          ...

        @some_decorator(arg_1='some-value')
        def method_2(self):
          ...

    Behind the scenes we actually call either the
    ``decorator_func`` or ``meta_func`` depending on the decorator declaration.

    The ``meta_func`` must also return a wrapper function that accepts a single
    argument and calls the original ``decorator_func`` with that arg.
    """

    def wrapper(*args, **kwargs):
        """
        Only allow 2 scenarios:

        1- Single arg, no kwargs and arg is a callable -> @decorator
        2- No args and some kwargs -> @decorator(foo='bar')

        Known issue: This will cause hilarious bugs if someone decides
        to do ``@decorator(some_callable)``, as at this point
        there is no way to figure out if the callable is the actual
        method that is being decorated or just an arbitrary callable.
        """
        if (args and kwargs) or (args and len(args) > 1):
            raise ValueError(
                'Only "@{func_name}" or "@{func_name}(**kwargs)" '
                "calls are allowed.".format(func_name=wrapper_func.__name__)
            )

        if args:
            if not callable(args[0]):
                raise ValueError(
                    "args[0] must be callable, it was {}".format(type(args[0]))
                )
            return decorator_func(args[0])
        return meta_func(**kwargs)

    return wrapper


def _number_of_testcases():
    """
    Number of testcases in a test suite.
    """
    return len(__TESTCASES__) + len(__GENERATED_TESTCASES__)


def _ensure_unique_generated_testcase_names(names, functions):
    """
    If function generation ends up with functions with duplicate names, this
    last step will make sure that they are differentiated by number suffixes.
    """
    name_counts = collections.Counter(
        itertools.chain(names, (func.__name__ for func in functions))
    )
    dupe_names = {k for k, v in name_counts.items() if v > 1}

    if len(dupe_names) == 0:
        return

    dupe_counter = collections.defaultdict(int)
    valid_names = set(names)

    for func in functions:
        name = func.__name__
        if name in dupe_names or name in valid_names:
            while True:
                func.__name__ = "{}__{}".format(name, dupe_counter[name])
                dupe_counter[name] += 1
                if (
                    func.__name__ not in dupe_names
                    and func.__name__ not in valid_names
                ):
                    valid_names.add(func.__name__)
                    break
        else:
            valid_names.add(func.__name__)

    # Functions should have different __name__ attributes after the step above
    name_counts = collections.Counter(
        itertools.chain(names, (func.__name__ for func in functions))
    )
    dupe_names = {k for k, v in name_counts.items() if v > 1}
    if len(dupe_names):
        raise RuntimeError(
            f"Internal error, duplicate case names found: {dupe_names}"
        )


def _testsuite(klass):
    """
    Actual decorator that transforms a class into a suite and registers
    testcases.
    """
    # nasty, but smallest possible evil that has to be perpetrated in order
    # to preserve the order of definition of the testcases and make sure
    # they get executed in the same order

    _ensure_unique_generated_testcase_names(
        __TESTCASES__ + __PARAMETRIZATION_TEMPLATE__, __GENERATED_TESTCASES__
    )

    klass.__testcases__ = [None] * _number_of_testcases()

    for testcase_name in __TESTCASES__:
        klass.__testcases__[
            getattr(klass, testcase_name).__seq_number__
        ] = testcase_name

    for func in __GENERATED_TESTCASES__:
        klass.__testcases__[func.__seq_number__] = func.__name__
        setattr(klass, func.__name__, func)

    assert all(testcase for testcase in klass.__testcases__)

    # Attributes `name` and `__tags__` and `strict_order` are added only when
    # class is decorated by @testsuite(...) with following parentheses.
    if not hasattr(klass, "name"):
        klass.name = None

    if callable(klass.name):
        try:
            interface.check_signature(klass.name, ["cls_name", "suite"])
        except interface.MethodSignatureMismatch as err:
            _reset_globals()
            raise err
    elif not (klass.name is None or isinstance(klass.name, str)):
        _reset_globals()
        raise TypeError('"name" should be a string or a callable or `None`')

    if not hasattr(klass, "__tags__"):
        klass.__tags__ = {}  # used for UI
        klass.__tags_index__ = {}  # used for actual filtering

    if not hasattr(klass, "strict_order"):
        klass.strict_order = False

    for func_name in __PARAMETRIZATION_TEMPLATE__:
        getattr(klass, func_name).strict_order = klass.strict_order

    klass.get_testcases = get_testcase_methods

    # propagate suite's native tags onto itself, which
    # will propagate them further to the suite's testcases
    propagate_tag_indices(klass, klass.__tags__)

    # Collect tag indices from testcase methods and update suite's tag index.
    update_tag_index(
        obj=klass,
        tag_dict=tagging.merge_tag_dicts(
            *[tc.__tags_index__ for tc in get_testcase_methods(klass)]
        ),
    )

    # Suite resolved, clear global variables for resolving the next suite.
    _reset_globals()

    setattr(
        klass,
        TESTSUITE_METADATA_ATTRIBUTE,
        TestSuiteStaticMetadata(LocationMetadata.from_object(klass)),
    )

    return klass


def _testsuite_meta(name=None, tags=None, strict_order=False):
    """
    Wrapper function that allows us to call :py:func:`@testsuite <testsuite>`
    decorator with extra arguments.
    """

    @functools.wraps(_testsuite)
    def wrapper(klass):
        """Meta logic for suite goes here."""
        klass.name = name

        if tags:
            klass.__tags__ = tagging.validate_tag_value(tags)
            klass.__tags_index__ = copy.deepcopy(klass.__tags__)
        else:
            klass.__tags__ = {}
            klass.__tags_index__ = {}

        klass.strict_order = strict_order

        return _testsuite(klass)

    return wrapper


def testsuite(*args, **kwargs):
    """
    Annotate a class as being a test suite.

    An :py:func:`@testsuite <testsuite>`-annotated class must have one or more
    :py:func:`@testcase <testcase>`-annotated methods. These methods will be
    executed in their order of definition. If a ``setup(self, env)`` and
    ``teardown(self, env)`` methods are present on the
    :py:func:`@testsuite <testsuite>`-annotated class, then they will be
    executed respectively before and after the
    :py:func:`@testcase <testcase>`-annotated methods have executed.

    :param name: Custom name to be used instead of class name for test suite
        in test report. A callable should has a signature like following:

        | name(cls_name: ``str``, suite: ``testsuite``) -> ``str``

        Where test suite class name will be passed to ``cls_name`` and
        instance of test suite class will be passed to ``suite``.
    :type name: ``str`` or ``callable``  or ``NoneType``
    :param tags: Allows filtering of tests with simple tags, or multi-simple
        tags, or named tags, or multi-named tags.
    :type tags: ``str`` or ``tuple(str)`` or ``dict( str: str)`` or
        ``dict( str: tuple(str))`` or ``NoneType``
    :param strict_order: Force testcases to run sequentially as they were
        defined in test suite.
    :type strict_order: ``bool``
    """
    return _selective_call(
        decorator_func=_testsuite,
        meta_func=_testsuite_meta,
        wrapper_func=testsuite,
    )(*args, **kwargs)


def _validate_function_name(func):
    """Validate the function name is valid for a testcase."""
    reserved_words = (
        "name",
        "get_testcases",
        "setup",
        "teardown",
        "pre_testcase",
        "post_testcase",
    )
    errmsg = None

    if (
        func.__name__ in __TESTCASES__
        or func.__name__ in __PARAMETRIZATION_TEMPLATE__
    ):
        errmsg = 'Duplicate testcase definition "{}" found'.format(
            func.__name__
        )

    elif func.__name__.startswith("__") and func.__name__.endswith("__"):
        errmsg = 'Cannot define testcase "{}" as a dunder method'.format(
            func.__name__
        )

    elif func.__name__ in reserved_words:
        errmsg = (
            "Testcase cannot be defined as any of the following"
            " because they are reserved by Testplan: {}."
        ).format(", ".join('"{}"'.format(word) for word in reserved_words))

    if errmsg is not None:
        _reset_globals()
        try:
            src_file = inspect.getsourcefile(func)
            src_line = inspect.getsourcelines(func)[1]
            raise ValueError("{} ({}:{})".format(errmsg, src_file, src_line))
        except IOError:
            raise ValueError(errmsg)


def _validate_testcase(func):
    """Validate the expected function signature of a testcase."""
    try:
        interface.check_signature(func, ["self", "env", "result"])

        if not isinstance(func.name, str):
            raise ValueError(
                'Testcase name "{name}" must be a string, it is of type:'
                " {type}".format(name=func.name, type=type(func.name))
            )
        elif not func.name:
            raise ValueError("Testcase name cannot be an empty string")

    except Exception as exc:
        _reset_globals()
        raise exc

    if len(func.name) > defaults.MAX_TEST_NAME_LENGTH:
        warnings.warn(
            'Name defined for testcase "{}" is too long,'
            ' consider customizing testcase name with argument "name_func"'
            " in @testcase decorator.".format(func.__name__)
        )


def _mark_function_as_testcase(func):
    func.__testcase__ = True


def _testcase(function):

    return _testcase_meta()(function)


def add_testcase_metadata(func: Callable, metadata: TestCaseStaticMetadata):
    setattr(func, TESTCASE_METADATA_ATTRIBUTE, metadata)


def _testcase_meta(
    name=None,
    tags=None,
    parameters=None,
    name_func=parametrization.default_name_func,
    tag_func=None,
    docstring_func=None,
    custom_wrappers=None,
    summarize=False,
    num_passing=defaults.SUMMARY_NUM_PASSING,
    num_failing=defaults.SUMMARY_NUM_FAILING,
    key_combs_limit=defaults.SUMMARY_KEY_COMB_LIMIT,
    execution_group=None,
    timeout=None,
):
    """
    Wrapper function that allows us to call :py:func:`@testcase <testcase>`
    decorator with extra arguments.
    """

    @functools.wraps(_testcase)
    def wrapper(function):
        """Actual decorator that validates & registers a method as a testcase."""
        global __TESTCASES__
        global __GENERATED_TESTCASES__
        global __PARAMETRIZATION_TEMPLATE__

        _validate_function_name(function)
        function.name = name or function.__name__

        tag_dict = tagging.validate_tag_value(tags) if tags else {}
        function.__tags__ = copy.deepcopy(tag_dict)
        function.__tags_index__ = copy.deepcopy(tag_dict)

        if parameters is not None:  # Empty tuple / dict checks happen later
            function.__parametrization_template__ = True
            __PARAMETRIZATION_TEMPLATE__.append(function.__name__)

            try:
                functions = parametrization.generate_functions(
                    function=function,
                    name=function.name,
                    parameters=parameters,
                    name_func=name_func,
                    docstring_func=docstring_func,
                    tag_func=tag_func,
                    tag_dict=tag_dict,
                    summarize=summarize,
                    num_passing=num_passing,
                    num_failing=num_failing,
                    key_combs_limit=key_combs_limit,
                    execution_group=execution_group,
                    timeout=timeout,
                )
            except parametrization.ParametrizationError as err:
                # Testplan stops execution if `ParametrizationError` raises.
                # However in our test the process will not quit but continue
                # to run the next testcase, and module will not be reloaded.
                # So, it is better reset globals before raising this error.
                _reset_globals()
                raise err

            # Register generated functions as testcases
            for func in functions:
                _validate_testcase(func)
                # this has to be called before wrappers otherwise wrappers can
                # fail if they rely on ``__testcase__``
                _mark_function_as_testcase(func)

                func.__seq_number__ = _number_of_testcases()
                func.__skip__ = []

                wrappers = custom_wrappers or []
                if not isinstance(wrappers, (list, tuple)):
                    wrappers = [wrappers]

                for wrapper_func in wrappers:
                    func = wrapper_func(func)

                __GENERATED_TESTCASES__.append(func)

                add_testcase_metadata(
                    func,
                    TestCaseStaticMetadata(
                        LocationMetadata.from_object(function)
                    ),
                )

            return function

        else:

            _validate_testcase(function)
            _mark_function_as_testcase(function)

            function.__seq_number__ = _number_of_testcases()
            function.__skip__ = []

            function.summarize = summarize
            function.summarize_num_passing = num_passing
            function.summarize_num_failing = num_failing
            function.summarize_key_combs_limit = key_combs_limit
            function.execution_group = execution_group
            function.timeout = timeout

            wrappers = custom_wrappers or []

            if not isinstance(wrappers, (list, tuple)):
                wrappers = [wrappers]

            for wrapper_func in wrappers:
                function = wrapper_func(function)

            __TESTCASES__.append(function.__name__)

            add_testcase_metadata(
                function,
                TestCaseStaticMetadata(LocationMetadata.from_object(function)),
            )
            return function

    return wrapper


def is_testcase(func):
    """
    Returns true if the given function is a testcase.
    :param func: Function object.

    :return: True if the function is decorated with testcase.
    """
    return hasattr(func, "__testcase__")


def testcase(*args, **kwargs):
    """
    Annotate a member function as being a testcase.

    This checks that the function takes three arguments called
    self, env, report and will throw if it's not the case.

    Although this is somewhat restrictive, it also lessens the chances that
    wrong signatures (with swapped parameters for example) will cause bugs
    that can be time-consuming to figure out.

    :param name: Custom name to be used instead of function name for testcase
        in test report. In case of a parameterized testcases, this custom name
        will be used as the parameterized group name in report.
    :type name: ``str`` or ``NoneType``
    :param tags: Allows filtering of tests with `simple tags` or
        `multi-simple tags` or `named tags` or `multi-named tags`.
    :type tags: ``str`` or ``tuple(str)`` or ``dict(str: str)`` or
        ``dict(str: tuple(str))`` or ``NoneType``
    :param parameters: Enables the creation of more compact testcases using
        simple or combinatorial paramatization, by allowing you to pass extra
        arguments to the testcase declaration.

        Note that the ``special_case`` must either be: a tuple or list with
        positional values that correspond to the parametrized argument names
        in the method definition OR a dict that has matching keys & values to
        the parametrized argument names OR a single value (that is not a tuple,
        or list) if and only if there is a single parametrization argument.
    :type parameters: ``list(object)`` or ``tuple(special_case)`` or
        ``dict(list(object)`` or ``tuple(object))`` or ``NoneType``
    :param name_func: Custom name generation algorithm for parametrized
        testcases. The callable should has a signature like following:

        | name_func(func_name: ``str``, kwargs: ``collections.OrderedDict``) -> ``str``

        Where parameterized group name (function name or as specified in name
        parameter) will be passed to ``func_name`` and input parameters will be
        passed to ``kwargs``.
    :type name_func: ``callable`` or ``NoneType``
    :param tag_func: Dynamic testcase tag assignment function that returns
        simple tags or named tag context. The signature is:

        | tag_func(kwargs: ``collections.OrderedDict``) -> ``dict`` or ``list``

        Where ``kwargs`` is an ordered dictionary of parametrized arguments.

        NOTE: If you use ``tag_func`` along with ``tags`` argument, Testplan
        will merge the dynamically generated tag context with the explicitly
        passed tag values.
    :type tag_func: ``callable`` or ``NoneType``
    :param docstring_func: Custom testcase docstring generation function. The
        signature is:

        | docstring_func(docstring: ``str`` or ``None``, kwargs: ``collections.OrderedDict``) -> ``str`` or ``None``

        Where ``docstring`` is document string of the parametrization target
        function, ``kwargs`` is an ordered dictionary of parametrized arguments.
    :type docstring_func: ``callable`` or ``NoneType``
    :param custom_wrappers: Wrapper to decorate parametrized testcases (used
        instead of @decorator syntax) that uses
        :py:func:`testplan.common.utils.callable.wraps`
    :type custom_wrappers: ``callable`` or ``NoneType``
    :param summarize: Whether the testcase should be summarized in its output
    :type summarize: ``bool``
    :param num_passing: The number of passing assertions reported per category
        per assertion type
    :type num_passing: ``int``
    :param num_failing: The number of failing assertions reported per category
        per assertion type
    :type num_failing: ``int``
    :param key_combs_limit: Max number of failed key combinations on fix/dict
        summaries.
    :type key_combs_limit: ``int``
    :param execution_group: Group of test cases to run in parallel with (
        groups overall are executed serially)
    :type execution_group: ``str`` or ``NoneType``
    :param timeout: Time elapsed in seconds until TimeoutException raised
    :type timeout: ``int`` or ``NoneType``
    """
    return _selective_call(
        decorator_func=_testcase,
        meta_func=_testcase_meta,
        wrapper_func=testcase,
    )(*args, **kwargs)


def _validate_skip_if_predicates(predicates):
    """
    Check for signature of functions, which  are used to set / extend
    ``skip_funcs`` attribute of the testcase method.
    """
    for predicate in predicates:
        try:
            interface.check_signature(predicate, ["testsuite"])
        except interface.MethodSignatureMismatch as err:
            _reset_globals()
            raise err


def skip_if(*predicates):
    """
    Annotate a testcase with skip predicate(s). The skip predicates will be
    evaluated before the testsuite is due to be executed and passed the
    instance of the suite as the sole argument.

    The predicate's signature must name the argument "testsuite" or
    a ``MethodSignatureMismatch`` will be raised.

    If any of the predicates is true, then the testcase will be skipped by
    MultiTest instead of being normally executed.
    """

    def skipper(testcase_method):
        """
        Inner implementation of skip
        """
        _validate_skip_if_predicates(predicates)
        testcase_method.__skip__ += predicates
        return testcase_method

    return skipper


def skip_if_testcase(*predicates):
    """
    Annotate a suite with skip predicate(s). The skip predicates will be
    evaluated against each test case method before the testsuite is due
    to be executed and passed the instance of the suite as the sole argument.

    The predicate's signature must name the argument "testsuite" or
    a ``MethodSignatureMismatch`` will be raised.

    If any of the predicates returns true for a test case method
    then the method will be skipped.
    """

    def _skip_if_testcase_inner(klass):
        _validate_skip_if_predicates(predicates)
        for testcase_method in get_testcase_methods(klass):
            testcase_method.__skip__ += predicates
        return klass

    return _skip_if_testcase_inner


def xfail(reason, strict=False):
    """
    Mark a testcase/testsuit as XFail(known to fail) when not possible to fix
    immediately. This decorator mandates a reason that explains why the test is
    marked as passed. XFail testcases will be highlighted as orange on testplan
    report.
    By default, should the test pass while we expect it to fail, the report
    will mark it as failed.
    For unstable tests, set ``strict`` to ``False``. Note that doing so
    decreases the value of the test.

    :param reason: Explains why the test is marked as passed.
    :type reason: ``str``
    :param strict: Should the test pass while we expect it to fail, the report
    will mark it as failed if strict is True,  default is False.
    :type strict: ``bool``
    """

    def _xfail_test(test):
        test.__xfail__ = {"reason": reason, "strict": strict}
        return test

    return _xfail_test


def timeout(seconds):
    """
    Decorator for non-testcase method in a test suite, can be used for
    setup, teardown, pre_testcase and post_testcase.
    """

    assert (
        isinstance(seconds, int) and seconds > 0
    ), "Invalid use of `suite.timeout`, argument must be a positive integer"

    def inner(function):
        function.timeout = seconds
        return function

    return inner


def get_testcase_metadata(testcase: object):
    static_metadata = getattr(
        testcase,
        TESTCASE_METADATA_ATTRIBUTE,
    )

    return TestCaseMetadata(
        **dataclasses.asdict(static_metadata),
        name=testcase.name,
        description=testcase.__doc__,
    )


def get_suite_metadata(suite: object) -> TestSuiteMetadata:
    static_metadata: TestSuiteStaticMetadata = getattr(
        suite, TESTSUITE_METADATA_ATTRIBUTE
    )
    testcase_metadata = [
        get_testcase_metadata(tc)
        for _, tc in inspect.getmembers(suite)
        if hasattr(tc, TESTCASE_METADATA_ATTRIBUTE)
    ]

    return TestSuiteMetadata(
        **dataclasses.asdict(static_metadata),
        name=suite.name,
        description=get_testsuite_desc(suite),
        test_cases=testcase_metadata,
    )
