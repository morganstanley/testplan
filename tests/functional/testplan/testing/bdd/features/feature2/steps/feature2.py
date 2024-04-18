from testplan.testing.bdd.step_registry import Given, When, Then


@Given("we have two numbers: {a} and {b}")
def step_definition(env, result, context, a, b):
    context.numbers = (int(a), int(b))


@When("we subtract the numbers")
def step_definition(env, result, context):
    context.result = context.numbers[0] - context.numbers[1]


@Then("the result is: {expected}")
def step_definition(env, result, context, expected):
    result.equal(context.result, int(expected))
