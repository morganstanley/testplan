from testplan.testing.bdd.step_registry import When


@When("we subtract the numbers")
def step_definition(env, result, context):
    context.result = context.numbers[0] - context.numbers[1]
