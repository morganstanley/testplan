from testplan.testing.bdd.step_registry import Given, Then


@Given("we have two numbers: {a} and {b}")
def step_definition(env, result, context, a, b):
    context.numbers = (int(a), int(b))


@Then("the result is: {expected}")
def step_definition(env, result, context, expected):
    result.equal(context.result, int(expected))
