from testplan.testing.bdd.step_registry import step


@step("the server is accepting connectons")
def step_definition(env, result, context):
    # Server accepts client connection.
    env.server.accept_connection()


@step("client send: {message}")
def step_definition(env, result, context, message):
    context.bytes_sent = env.client.send_text(message)


@step("the server receive: {message}")
def step_definition(env, result, context, message):
    received = env.server.receive_text(size=context.bytes_sent)
    result.equal(received, message, "Server received")


@step("the server respond with: {response}")
def step_definition(env, result, context, response):
    context.bytes_sent = env.server.send_text(response)


@step("the client got: {response}")
def step_definition(env, result, context, response):
    received = env.client.receive_text(size=context.bytes_sent)
    result.equal(received, response, "Client received")
