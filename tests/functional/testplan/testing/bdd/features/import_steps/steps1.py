from testplan.testing.bdd.step_registry import import_steps, step

import_steps("./common.py")
import_steps("./common/common2.py")


@step("steps1")
def step(env, result, context):
    pass
