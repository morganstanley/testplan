from testplan.testing.bdd.step_registry import step


@step("we have two number: {a} and {b}")
def step_definition(env, result, context, a, b):
    context.numbers = (int(a), int(b))


@step("we sum the numbers")
def step_definition(env, result, context, detail):
    context.result = sum(context.numbers)
    result.equal(
        f"with a of value {context.numbers[0]} and b of value {context.numbers[1]}",
        detail,
    )


@step("the result is: {expected}")
def step_definition(env, result, context, expected):
    result.equal(context.result, int(expected))


@step("our small table looks good")
def step_definition(env, result, context, table):
    r = list(table.rows())[0]
    result.equal(r.a, str(context.numbers[0]))
    result.equal(r.b, str(context.numbers[1]))
    result.equal(r.expected, str(context.result))
