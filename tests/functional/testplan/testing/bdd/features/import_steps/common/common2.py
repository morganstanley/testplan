from testplan.testing.bdd.step_registry import import_steps, step

import_steps("../utils/utils.py")


@step("common2")
def step(env, result, context):
    pass
