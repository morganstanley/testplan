import threading

from testplan.testing.bdd.step_registry import step


@step("thread id is logged")
def step_definition(env, result, context):
    result.log(
        f"{threading.current_thread().name}: {threading.current_thread().ident}"
    )


@step("we have two number: {a} and {b}")
def step_definition(env, result, context, a, b):
    context.numbers = (int(a), int(b))


@step("we sum the numbers")
def step_definition(env, result, context):
    context.result = sum(context.numbers)


@step("the result is: {expected}")
def step_definition(env, result, context, expected):
    result.equal(context.result, int(expected))
