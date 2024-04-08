from testplan.testing.bdd.step_registry import When, import_steps

import_steps("common.py")


@When("one salute")
def step_definition(env, result, context):
    context.salute = "Hello {}".format(context.name)
