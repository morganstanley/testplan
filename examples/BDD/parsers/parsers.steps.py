from testplan.testing.bdd.parsers import SimpleParser, RegExParser
from testplan.testing.bdd.step_registry import step, set_actual_parser


# Using a parser can be explicit


@step(SimpleParser("_SP explicit match"))
def step_definition(env, result, context):
    pass


@step(RegExParser("^_RP explicit match$"))
def step_definition(env, result, context):
    pass


# it can capture things from the sentence


@step(SimpleParser("_SP explicit match and log name: {name}"))
def step_definition(env, result, context, name):
    result.log(name)


@step(RegExParser("_RP explicit match and log name: (?P<name>.*)"))
def step_definition(env, result, context, name):
    result.log(name)


# The default is RegExParser


@step("^_RP as default match$")
def step_definition(env, result, context):
    pass


@step("_RP as default match and log name: (?P<name>.*)")
def step_definition(env, result, context, name):
    result.log(name)


# one can override the parser for a portion of the step definition file

set_actual_parser(SimpleParser)


@step("_SP as override match")
def step_definition(env, result, context):
    pass


@step("_SP as override match and log name: {name}")
def step_definition(env, result, context, name):
    result.log(name)


# and change back to RegExParser
set_actual_parser(RegExParser)


@step("_RP (?:to match this|and this too)")
def step_definition(env, result, context):
    result.log("multiple sentence matcher")
