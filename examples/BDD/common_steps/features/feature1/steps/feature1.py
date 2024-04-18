from testplan.testing.bdd.step_registry import When


@When("we sum the numbers")
def step_definition(env, result, context):
    context.result = sum(context.numbers)
