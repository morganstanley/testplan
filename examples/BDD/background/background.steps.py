from testplan.testing.bdd.step_registry import step

# This is the function to test
def salute(format_str, first_name, last_name):
    return format_str.format(first_name=first_name, last_name=last_name)


# With these formats of salute
FORMATS = {
    "hi": "Hi {first_name} {last_name}",
    "hello": "Hello {last_name} {first_name}",
}


@step("we have {key} as {value}")
def step_definition(env, result, context, key, value):
    context[key] = value


@step("we say {salute_format}")
def step_definition(env, result, context, salute_format):
    context.result = salute(
        FORMATS[salute_format], context.first_name, context.last_name
    )


@step('it sounds: "{expected}"')
def step_definition(env, result, context, expected):
    result.equal(context.result, expected)
