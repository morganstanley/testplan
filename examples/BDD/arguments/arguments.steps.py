from testplan.testing.bdd.step_registry import step


@step("we log a complex formatted string:")
def step_definition(env, result, context, argument):
    # argument here is an str as it is passed as a python stile docstring
    result.log(argument)


@step("we have a table and we nicely log it:")
def step_definition(env, result, context, argument):
    # argument here is a DataTable
    result.table.log(list(argument.rows()))


@step("we fill the format with name: {name}")
def step_definition(env, result, context, argument, name):
    context.result = argument % name


@step('the result is "{expected}"')
def step_definition(env, result, context, expected):
    result.equal(context.result, expected)
