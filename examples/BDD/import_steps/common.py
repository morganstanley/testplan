from testplan.testing.bdd.step_registry import Given, Then


@Given("my name is {name}")
def step_definition(env, result, context, name):
    context.name = name


@Then("I hear: {salute}")
def step_definition(env, result, context, salute):
    result.equal(context.salute, salute)
