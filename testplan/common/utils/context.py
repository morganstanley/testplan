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
    and a Jinja2 template, to be resolved on driver start.
    """

    def __init__(self, driver: str, value: str):
        """
        Create a new context value
        """
        self.driver = driver
        self.value = value
        self.template = parse_template(value)

    def __str__(self):
        return f"context('{self.driver}', '{self.value}')"

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
    expression. Value expressions must be valid Jinja2 templates,
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


def render(template: Union[Template, TempitaTemplate, str], context) -> str:
    """
    Renders the template with the given context, that used for expression resolution.

    :param template: A template in str, Jinja2 or Tempita form that will be rendered with the context
    :type template: Union[Template, TempitaTemplate, str]
    :param context: The context object which is the base context of the template expansion
    :return: The rendered template
    :rtype: str
    """
    if isinstance(template, str):
        template = parse_template(template)

    return (
        template.substitute(context)
        if isinstance(template, TempitaTemplate)
        else template.render(context)
    )
