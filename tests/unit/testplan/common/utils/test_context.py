from unittest.mock import Mock

import pytest
from jinja2 import Template
from testplan.vendor.tempita import Template as TempitaTemplate
from pytest import fixture

from testplan.common.utils.context import (
    ContextValue,
    expand,
    expand_env,
    render,
)


@fixture(scope="module")
def driver_context():
    mock = Mock()
    mock.context_input = Mock(return_value=dict(host="host.ms.com", port=123))
    return {"driver": mock}


def test_constructor_with_Jinja(driver_context):
    cv = ContextValue("driver", "{{host}}")
    assert isinstance(cv.template, Template)
    value = cv(driver_context)
    assert value == "host.ms.com"

    cv = ContextValue("driver", "{{host}}:{{port}}")
    assert isinstance(cv.template, Template)
    value = cv(driver_context)
    assert value == "host.ms.com:123"


def test_constructor_with_Tempita(driver_context):
    cv = ContextValue("driver", "{{if port > 1}}{{host}}{{endif}}")
    assert isinstance(cv.template, TempitaTemplate)
    value = cv(driver_context)
    assert value == "host.ms.com"

    cv = ContextValue(
        "driver", "{{if port > 123}}{{host}}{{else}}{{port}}{{endif}}"
    )
    assert isinstance(cv.template, TempitaTemplate)
    value = cv(driver_context)
    assert value == "123"


def test_constructor_with_Invalid():
    with pytest.raises(Exception):
        cv = ContextValue("driver", 123)


def test_missing_driver(driver_context):
    with pytest.raises(RuntimeError):
        cv = ContextValue("driver2", "{{port}}")
        cv(driver_context)


def test_expand(driver_context):
    assert expand(12, driver_context) == 12
    assert expand("str", driver_context) == "str"
    cv = ContextValue("driver", "{{port}}")
    assert expand(cv, driver_context) == "123"
    assert expand(cv, driver_context, int) == 123


def test_expand_env(driver_context):
    env = dict(a="1", b="2")
    overrides = dict(
        c="str",
        d="{{notcontext}}",
        e=ContextValue("driver", "{{host}}"),
        b=ContextValue("driver", "{{port}}"),
    )
    result = expand_env(env, overrides, driver_context)

    assert result["a"] == "1"
    assert result["b"] == "123"
    assert result["c"] == "str"
    assert result["d"] == "{{notcontext}}"
    assert result["e"] == "host.ms.com"


def test_render():
    context = dict(a="1", b=2)
    expected = "1:2"
    template = "{{a}}:{{b}}"

    assert render(template, context) == expected
    assert render(TempitaTemplate(template), context) == expected
    assert render(Template(template), context) == expected
