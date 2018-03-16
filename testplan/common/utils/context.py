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


class ContextValue(object):
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
            raise ValueError('Could not retrieve driver {0} value from '
                             'NoneType context.'.format(self.driver))
        if self.driver not in ctx:
            raise Exception('Driver {0} is not present in context.'.format(
                self.driver))
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
