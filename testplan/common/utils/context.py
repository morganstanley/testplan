"""TODO."""

from testplan.vendor.tempita import Template


def expand(value, contextobj, constructor=None):
    """
    Take a value and a context and return the expanded result.
    Apply a constructor if necessary.
    """
    if is_context(value):
        expanded_value = value(contextobj)
        if constructor:
            expanded_value = constructor(expanded_value)
        return expanded_value
    else:
        return value


def expand_env(orig, overrides, contextobj):
    """
    Copies the `orig` dict of environment variables.
    Applies specified overrides.
    Removes keys that have value of None as override.
    Expands context values as strings.
    Returns as a copy.

    :param orig: The initial environment variables. Usually `os.environ` is to
                 be passed in. This will not be modified.
    :type orig: ``dict`` of ``str`` to ``str``
    :param overrides: Keys and values to be overriden. Values can be strings or
                      context objects.
    :type overrides: ``dict`` of ``str`` to either ``str`` or ``ContextValue``
    :param contextobj: The context object that can be used to expand context
                       values.
    :type contextobj: ``object``

    :return: Copied, overridden and expanded environment variables
    :rtype: ``dict``
    """
    env = orig.copy()
    env.update(overrides)
    return {
        key: expand(val, contextobj, str)
        for key, val in env.items()
        if val is not None
    }


class ContextValue:
    """
    A context value represents a combination of a driver name
    and a tempita template, to be resolved on driver start.
    """

    def __init__(self, driver, value):
        """
        Create a new context value
        """
        self.driver, self.value = driver, Template(value)

    def __call__(self, ctx):
        """
        Resolve the template.
        """
        if ctx is None:
            raise ValueError(
                f'Could not retrieve driver "{self.driver}" value'
                " from NoneType context."
            )
        if self.driver not in ctx:
            raise RuntimeError(
                f'Driver "{self.driver}" is not present in context.'
            )
        return self.value.substitute(ctx[self.driver].context_input())


def context(driver, value):
    """
    Create a context extractor from a driver name and a value
    expression. Value expressions must be valid tempita templates,
    which will be resolved from the context.
    """
    return ContextValue(driver, value)


def is_context(value):
    """
    Checks if a value is a context value
    :param value: Value which may have been constructed through `context`
    :type value: ``object``

    :return: True if it is a context value, otherwise False
    :rtype: ``bool``
    """
    return isinstance(value, ContextValue)
