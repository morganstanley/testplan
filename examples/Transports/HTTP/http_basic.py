"""Tests HTTP requests between a server and a client."""
import json

from testplan.common.utils.context import context

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.http import (
    HTTPServer,
    HTTPClient,
    HTTPResponse,
)


@testsuite
class HTTPTestsuite:
    """HTTP requests between a server and a client."""

    @testcase
    def request_and_response(self, env, result):
        """
        Client makes a request, server received and responds back.
        """
        # The HTTPClient sends a GET request to some section of the API. The
        # HTTPServer will respond with the next message in it's response queue
        # no matter the HTTP method (GET, POST etc.) or the section of the API
        # it has been sent.
        result.log("Client sends GET request")
        env.http_client.get(api="/random/text")

        # Create some JSON.
        json_content = {"this": ["is", "a", "json", "object"]}

        # We then prepare an HTTPResponse. Headers are added as a dictionary and
        # content as a list. For this example we just indicate that the content
        # type is JSON and dump the JSON as a string so it can be sent.
        prepared_response = HTTPResponse(
            headers={"Content-type": "application/json"},
            content=[json.dumps(json_content)],
        )

        # The HTTPServer then responds. Under the hood this adds the response to
        # the HTTPServer's response queue which will be immediately sent as the
        # HTTPClient has already sent a request.
        result.log("Server receives request and sends response")
        env.http_server.respond(prepared_response)

        # The HTTPClient then receives the HTTPServer's response.
        response = env.http_client.receive()

        # We are verifying the JSON sent back is the same as the one sent by the
        # HTTPServer.
        result.dict.match(
            response.json(), json_content, "JSON response from server"
        )


def get_multitest(name):
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and a client connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    test = MultiTest(
        name=name,
        suites=[HTTPTestsuite()],
        environment=[
            HTTPServer(name="http_server"),
            HTTPClient(
                name="http_client",
                host=context("http_server", "{{host}}"),
                port=context("http_server", "{{port}}"),
            ),
        ],
    )
    return test
