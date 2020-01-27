"""Tests using a custom HTTP response handler."""
from testplan.common.utils.context import context

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.http import HTTPServer, HTTPClient

from custom_http_request_handler import CustomHTTPRequestHandler


@testsuite
class HTTPTestsuite(object):
    """Sending requests to an HTTPServer with a custom HTTP request handler."""

    @testcase
    def general_request(self, env, result):
        """
        Client makes a general request, server responds with text file contents.
        """
        # The HTTPClient sends a GET request to some section of the API.
        result.log("Client sends GET request")
        env.http_client.get(api="/random/text")

        # The HTTPServer will use the CustomHTTPRequestHandler to automatically
        # send the contents of the test.txt file back to every request. The
        # HTTPClient receives the HTTPServer's response.
        response = env.http_client.receive()

        # We are verifying the contents of the test.txt file is what the server
        # has sent back.
        text = open("test.txt").read()
        result.equal(
            response.text, text, "HTTPServer sends file contents in response."
        )

    @testcase
    def post_request(self, env, result):
        """
        Client makes a POST request, server responds with custom POST response.
        """
        result.log("Client sends POST request")
        env.http_client.post(api="/random/text")

        response = env.http_client.receive()

        result.equal(
            response.text,
            "POST response.",
            "HTTPServer sends custom POST response.",
        )


def get_multitest(name):
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and a client connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    # The HTTPServer can be passed handler_attributes in a dictionary. These
    # will be accessible in the custom HTTP request handler
    # (see custom_http_request_handler.py).
    attributes = {"text_file": "test.txt"}
    test = MultiTest(
        name=name,
        suites=[HTTPTestsuite()],
        environment=[
            HTTPServer(
                name="http_server",
                request_handler=CustomHTTPRequestHandler,
                handler_attributes=attributes,
            ),
            HTTPClient(
                name="http_client",
                host=context("http_server", "{{host}}"),
                port=context("http_server", "{{port}}"),
            ),
        ],
    )
    return test
