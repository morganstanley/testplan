import json
import random

from testplan.testing.bdd.step_registry import step


NAMES = ["Jane", "John", "Marvin", "Grace"]


def salute(name):
    return "Hello {}".format(name)


@step('"{value}" is stored in the context as {name}')
def step_definition(env, result, context, value, name):
    context[name] = value


@step("a random name as {name}")
def step_definition(env, result, context, name):
    context[name] = random.choice(NAMES)
    result.log("Random {}: {}".format(name, context[name]))


@step('salute is called with "{name}"')
def step_definition(env, result, context, name):
    context.result = salute(name)


@step("salute is called with:")
def step_definition(env, result, context, arg):
    context.result = salute(arg)


@step("salute is called with names:")
def step_definition(env, result, context, args):
    row = next(args.rows())
    context.result = salute("{} {}".format(row.firstname, row.middlename))


@step("salute is called with name parts:")
def step_definition(env, result, context, args):
    parts = args.dict()
    context.result = salute(
        "{} {} {}".format(
            parts["firstname"], parts["midname"], parts["lastname"]
        )
    )


@step('the result is "{expected}"')
def step_definition(env, result, context, expected):
    result.equal(context.result, expected)


@step("a json document as {doc_name}:")
def step_definition(env, result, context, json_input, doc_name):
    context[doc_name] = json.loads(json_input)
