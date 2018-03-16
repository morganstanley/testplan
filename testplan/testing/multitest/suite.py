"""Multitest testsuite/testcase module."""
import functools
import inspect
import traceback
from collections import defaultdict, OrderedDict

from testplan import defaults
from testplan.common.utils.callable import getargspec, wraps
from testplan.common.utils.interface import (method, MethodSignature,
                                             static_method,
                                             MethodSignatureMismatch)
from testplan.common.utils.strings import format_description
from testplan.testing import tagging
from . import parametrization


__GENERATED_TESTCASES__ = []
__TESTCASES__ = []
__SKIP__ = defaultdict(tuple)


def get_testsuite_name(suite):
    """
    Returns the name to be used for the given testsuite. This is made of
    the class name and the result of "suite_name()" method if this exists

    :param suite: Suite object whose name is needed
    :type suite: ``testsuite``

    :return: Name of given suite
    :rtype: ``str``
    """
    name = suite.__class__.__name__
    if hasattr(suite, 'suite_name') and\
          callable(getattr(suite, 'suite_name')) and\
                suite.suite_name() is not None:
        return '{} - {}'.format(name, suite.suite_name())
    return name


def get_testsuite_desc(suite):
    """
    Return the description of the testsuite.

    Remove trailing line returns if applicable, they look nasty
    in the reports (text and otherwise)
    """
    desc = suite.__doc__
    return format_description(desc.rstrip()) if desc else None


def set_testsuite_testcases(suite):
    """
    Build the list of testcases to run for the given testsuite

    :param suite: Suite object whose testcases need to be set
    :type suite: ``testsuite``

    :return: ``None``
    :rtype: ``NoneType``
    """
    testcases = []
    for testcase_name in suite.__class__.__testcases__:
        testcase_method = getattr(suite, testcase_name)

        if not testcase_method:
            msg = '{} does not have a testcase method named: {}'.format(
                suite, testcase_name)
            raise AttributeError(msg)

        if testcase_name in testcases:
            offending_obj = getattr(suite, testcase_name)
            try:
                raise ValueError(
                    "Duplicate definition of {}.{} at {}:{}".format(
                        suite.__class__.__name__,
                        testcase_name,
                        inspect.getsourcefile(offending_obj),
                        inspect.getsourcelines(offending_obj)[1]
                    )
                )
            except IOError:
                raise ValueError(
                    "Duplicate definition of {}.{}".format(
                        suite.__class__.__name__, testcase_name))

        skip_funcs = suite.__skip__[testcase_name]
        if not any(skip_func(suite) for skip_func in skip_funcs):
            testcases.append(testcase_name)
    setattr(suite, '__testcases__', testcases)


def get_testcase_desc(suite, testcase_name):
    """
    Return the description of the testcase with the given name of the
    given testsuite.

    Remove trailing line returns if applicable, they look nasty
    in the reports (text and otherwise)
    """
    desc = getattr(suite, testcase_name).__doc__
    return format_description(desc.rstrip()) if desc else ''


@classmethod
def get_testsuite_testcase_methods(testsuite_kls):
    """
    Return the unbound method objects marked as a testcase
    from a testsuite class.
    """

    if not hasattr(testsuite_kls, '__testcases__'):
        raise AttributeError('Testsuite does not have any testcases set yet.')

    return OrderedDict([(testcase_name, getattr(testsuite_kls, testcase_name))
                        for testcase_name in testsuite_kls.__testcases__
                        if callable(getattr(testsuite_kls, testcase_name))])


def get_testsuite_testcases(suite):
    """
    Return bound method objects from a test suite instance.

    The dictionary returned by this function may have different keys
    than the one that's returned by :py:func:`get_testsuite_testcase_methods`,
    as ``__testcases__`` per instance can change after filtering / shuffling
    logic is applied.
    """
    return OrderedDict((testcase_name, getattr(suite, testcase_name))
                       for testcase_name in suite.__testcases__)


def _selective_call(decorator_func, meta_func, wrapper_func):
    """
    This hacky higher order function gives us the flexibility of using the
    'same' decorator with or without extra arguments. So both declarations will
    be valid:

    .. code-block:: python

      class Foo(object):

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
                'Only `@{func_name}` or `@{func_name}(**kwargs)` '
                'calls are allowed.'.format(func_name=wrapper_func.__name__))

        if args:
            if not callable(args[0]):
                raise ValueError('args[0] must be callable, it was {}'.format(
                    type(args[0])))
            return decorator_func(args[0])
        return meta_func(**kwargs)
    return wrapper


def _testsuite(klass):
    """
    Actual decorator that transforms a class into a suite and registers
    testcases.
    """
    # nasty, but smallest possible evil that has to be perpetrated in order
    # to preserve the order of definition of the testcases and make sure
    # they get executed in the same order

    # pylint: disable=global-statement
    global __GENERATED_TESTCASES__
    global __TESTCASES__
    global __SKIP__
    klass.__testcases__ = __TESTCASES__
    klass.__skip__ = __SKIP__

    # Dynamically add a method for getting unbound & bound testcase methods
    klass.get_testcase_methods = get_testsuite_testcase_methods
    klass.get_testcases = get_testsuite_testcases

    for func in __GENERATED_TESTCASES__:
        setattr(klass, func.__name__, func)

    __GENERATED_TESTCASES__ = []
    __TESTCASES__ = []
    __SKIP__ = defaultdict(tuple)
    return klass


def _testsuite_meta(tags=None):
    """
    Wrapper function that allows us to call :py:func:`@testsuite <testsuite>`
    decorator with extra arguments.
    """

    @functools.wraps(_testsuite)
    def wrapper(klass):
        """Meta logic for suite goes here"""
        # need to create the suite first
        # as following functionality depends on attached methods
        suite = _testsuite(klass)

        if tags:
            tagging.attach_suite_tags(suite, tags)
        return suite
    return wrapper


def testsuite(*args, **kwargs):
    """
    Annotate a class as being a test suite

    An :py:func:`@testsuite <testsuite>`-annotated class must have one or more
    :py:func:`@testcase <testcase>`-annotated methods. These methods will be
    executed in their order of definition. If a ``setup(self, env)`` and
    ``teardown(self, env)`` methods are present on the
    :py:func:`@testsuite <testsuite>`-annotated class, then they will be
    executed respectively before and after the
    :py:func:`@testcase <testcase>`-annotated methods have executed.

    It is possible to assign tags to a suite via `@testsuite(tags=...)` syntax:

    .. code-block:: python

      @testsuite(tags=('server', 'keep-alive'))
      class SampleSuite(object):
        ...
    """
    return _selective_call(
        decorator_func=_testsuite,
        meta_func=_testsuite_meta,
        wrapper_func=testsuite,
    )(*args, **kwargs)


def _validate_testcase(func):
    refsig = method(func.__name__, ['env', 'result'])
    actualsig = MethodSignature(func.__name__,
                                getargspec(func),
                                lambda x: x)

    if refsig != actualsig:
        raise MethodSignatureMismatch('Expected {0}, not {1}'.format(
            refsig, actualsig))


def _mark_function_as_testcase(func):
    func.__testcase__ = True


def _testcase(func):
    """Actual decorator that validates & registers a method as a testcase."""
    _validate_testcase(func)
    _mark_function_as_testcase(func)
    __TESTCASES__.append(func.__name__)
    return func


def _testcase_meta(
    tags=None,
    parameters=None,
    name_func=parametrization.default_name_func,
    tag_func=None,
    docstring_func=None,
    custom_wrappers=None,
    summarize=False,
    num_passing=defaults.SUMMARY_NUM_PASSING,
    num_failing=defaults.SUMMARY_NUM_FAILING,
):
    """
    Wrapper function that allows us to call :py:func:`@testcase <testcase>`
    decorator with extra arguments.
    """
    @functools.wraps(_testcase)
    def wrapper(function):
        """Meta logic for test case goes here"""

        if tags:
            tagging.attach_testcase_tags(function, tags)

        if parameters is not None:  # Empty tuple / dict checks happen later

            functions = parametrization.generate_functions(
                function=function,
                parameters=parameters,
                name_func=name_func,
                docstring_func=docstring_func,
                tag_func=tag_func,
                tags=tags,
                summarize=summarize,
                num_passing=defaults.SUMMARY_NUM_PASSING,
                num_failing=defaults.SUMMARY_NUM_FAILING
            )

            # Register generated functions as test_cases
            for func in functions:
                _validate_testcase(func)
                # this has to be called before wrappers otherwise wrappers can
                # fail if they rely on __testcase__
                _mark_function_as_testcase(func)

                wrappers = custom_wrappers or []

                if not isinstance(wrappers, (list, tuple)):
                    wrappers = [wrappers]

                for wrapper_func in wrappers:
                    func = wrapper_func(func)

                # so that CodeDetails gets the correct line number
                func.wrapper_of = function

                __TESTCASES__.append(func.__name__)
                __GENERATED_TESTCASES__.append(func)

            # Assign tags (native & tags collected from generated functions)
            function.generated_tags = tagging.merge_tag_dicts(*[
                tagging.get_native_testcase_tags(func)
                for func in functions])
            return function
        else:
            function.summarize = summarize
            function.summarize_num_passing = num_passing
            function.summarize_num_failing = num_failing

            return _testcase(function)
    return wrapper


def is_testcase(func):
    """
    Returns true if the given function is a testcase.
    :param func: Function object.

    :return: True if the function is decorated with testcase.
    """
    return hasattr(func, '__testcase__')


def testcase(*args, **kwargs):
    """
    Annotate a member function as being a testcase

    This checks that the function takes three arguments called
    self, env, report and will throw if it's not the case.

    Although this is somewhat restrictive, it also lessens the chances that
    wrong signatures (with swapped parameters for example) will cause bugs
    that can be time-consuming to figure out.

    It is possible to assign tags to a suite via `@testcase(tags=...)` syntax:

    .. code-block:: python

      @testsuite
      class SampleSuite(object):

        @testcase(tags=('server', 'keep-alive'))
        def test_method_1(self):
          ...

    """
    return _selective_call(
        decorator_func=_testcase,
        meta_func=_testcase_meta,
        wrapper_func=testcase
    )(*args, **kwargs)


def _validate_skip_if_predicates(predicates):
    """
    Check for method signature, set / extend ``skip_funcs`` attribute of
    the testcase method.
    """
    for predicate in predicates:
        refsig = static_method(predicate.__name__, ['suite'])
        actualsig = MethodSignature(
            predicate.__name__, getargspec(predicate), lambda x: x)

        if refsig != actualsig:
            raise MethodSignatureMismatch('Expected {0}, not {1}'.format(
                refsig, actualsig))

    return predicates


def skip_if(*predicates):
    """
    Annotate a testcase with skip predicate(s). The skip predicates will be
    evaluated before the testsuite is due to be executed and passed the
    instance of the suite as the sole argument.

    The predicate's signature must name the argument "suite" or
    a ``MethodSignatureMismatch`` will be raised.

    If any of the predicates is true, then the testcase will be skipped by
    MultiTest instead of being normally executed.
    """

    def skipper(testcase_method):
        """
        Inner implementation of skip
        """
        result = _validate_skip_if_predicates(predicates)
        __SKIP__[testcase_method.__name__] += result
        return testcase_method
    return skipper


def _get_kwargs(kwargs, testcase_method):
    """Compatibility with parametrization"""
    return dict(kwargs,
                **getattr(testcase_method, '_parametrization_kwargs', {}))


def _gen_testcase_with_pre(testcase_method, preludes):
    """
    Attach prelude(s) to a testcase method

    :param testcase_method: a testcase method
    :param prelude: a callable with a compatible signature

    :return: testcase with prelude attached
    """
    wraps(testcase_method)
    def testcase_with_pre(*args, **kwargs):
        """
        Testcase with prelude
        """
        for prelude in preludes:
            prelude(testcase_method.__name__,
                    *args,
                    **_get_kwargs(kwargs, testcase_method))
        return testcase_method(*args, **kwargs)
    return testcase_with_pre


def run_epilogues(epilogues, name, *args, **kwargs):
    """
    Run epilogue and print related exception
    """
    for epilogue in epilogues:
        try:
            epilogue(name, *args, **kwargs)
        except Exception:
            print("Exception when running epilogue for {}".format(name))
            traceback.print_exc()


def _gen_testcase_with_post(testcase_method, epilogues):
    """
    Attach an epilogue to a testcase method

    :param testcase_method: a testcase method
    :param epilogue: a callable with a compatible signature

    :return: testcase with epilogue attached
    """
    @wraps(testcase_method)
    def testcase_with_post(*args, **kwargs):
        """
        Testcase with epilogue
        """
        epilogue_kwargs = _get_kwargs(kwargs, testcase_method)
        try:
            testcase_method(*args, **kwargs)
        except Exception:
            run_epilogues(epilogues, testcase_method.__name__,
                          *args, **epilogue_kwargs)
            raise
        else:
            run_epilogues(epilogues, testcase_method.__name__,
                          *args, **epilogue_kwargs)
    return testcase_with_post


def skip_if_testcase(*predicates):
    """
    Annotate a suite with skip predicate(s). The skip predicates will be
    evaluated against each test case method before the testsuite is due
    to be executed and passed the instance of the suite as the sole argument.

    The predicate's signature must name the argument "suite" or
    a ``MethodSignatureMismatch`` will be raised.

    If any of the predicates returns true for a test case method
    then the method will be skipped.
    """
    def _skip_if_testcase_inner(klass):
        _validate_skip_if_predicates(predicates)
        for testcase_method in klass.get_testcase_methods().values():
            klass.__skip__[testcase_method.__name__] += predicates
        return klass
    return _skip_if_testcase_inner


def pre_testcase(*functions):
    """
    Prepend callable(s) to trigger before every testcase in a testsuite

    :param func: a callable to be executed immediately before each testcase

    :return: testsuite with pre_testcase behaviour installed
    """

    def pre_testcase_inner(klass):
        """
        Inner part of class decorator
        """
        for testcase_method in klass.get_testcase_methods().values():
            twp = _gen_testcase_with_pre(testcase_method, functions)
            setattr(klass, testcase_method.__name__, twp)
        return klass

    return pre_testcase_inner


def post_testcase(*functions):
    """
    Append callable(s) to trigger after every testcase in a testsuite

    :param func: a callable to be executed immediately after each testcase

    :return: testsuite with post_testcase behaviour installed
    """

    def post_testcase_inner(klass):
        """
        Inner part of class decorator
        """
        for testcase_method in klass.get_testcase_methods().values():
            twp = _gen_testcase_with_post(testcase_method, functions)
            setattr(klass, testcase_method.__name__, twp)
        return klass

    return post_testcase_inner
