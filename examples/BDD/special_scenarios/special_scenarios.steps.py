from testplan.testing.bdd.step_registry import step


def salute(name):
    return "Hello {}".format(name)


@step("we log {message}")
def step_definition(env, result, context, message):
    result.log(message)


@step('salute is called with "{name}"')
def step_definition(env, result, context, name):
    context.result = salute(name)


@step('"{value}" is stored in the context as {name}')
def step_definition(env, result, context, value, name):
    context[name] = value


@step('the result is "{expected}"')
def step_definition(env, result, context, expected):
    result.equal(context.result, expected)
