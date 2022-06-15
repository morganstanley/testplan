"""TODO."""
import warnings
from typing import Union, Dict

from testplan.vendor.tempita import Template as TempitaTemplate
from jinja2 import Template


def parse_template(template: str) -> Union[TempitaTemplate, Template]:
    tempita_failed = False
    parsed_template = None
    try:
        parsed_template = Template(template)
    except Exception:
        try:
            # Jinja failed try with tempita
            parsed_template = TempitaTemplate(template)
        except Exception:
            tempita_failed = True
        else:
            tempita_warning = f"The template: '{template}' is not a valid Jinja2 template. Falling back to Tempita. Tempita will be decommisioned soon, please update your template."
            warnings.warn(tempita_warning, FutureWarning)
            pass
        finally:
            if tempita_failed:
                # raise the original jinja exception so user will fix it for jinja
                raise

    return parsed_template


class ContextValue:
    """
    A context value represents a combination of a driver name
    and a tempita template, to be resolved on driver start.
    """

    def __init__(self, driver: str, value: str):
        """
        Create a new context value
        """
        self.driver = driver
        self.template = parse_template(value)

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
        return render(self.template, ctx[self.driver].context_input())


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


def expand_env(
    orig: Dict[str, str],
    overrides: Dict[str, Union[str, ContextValue]],
    contextobj,
):
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


def render(template: Union[Template, TempitaTemplate, str], context):
    if isinstance(template, str):
        template = parse_template(template)

    return (
        template.substitute(context)
        if isinstance(template, TempitaTemplate)
        else template.render(context)
    )
