"""Custom HTTP request handler."""
from testplan.testing.multitest.driver.http import (
    HTTPRequestHandler,
    HTTPResponse,
)


class CustomHTTPRequestHandler(HTTPRequestHandler):
    """Define a custom request handler."""

    def get_response(self, request):
        """
        Override the get_response method to determine how the server will
        respond to all requests. You must return an HTTPResponse object as the
        _parse_request method expects this.
        """
        text_file = self.server.handler_attributes["text_file"]
        with open(text_file) as input:
            text = input.read()
        response = HTTPResponse(content=[text])
        self.server.log_callback(
            "Creating custom response from {}".format(text_file)
        )
        return response

    def do_POST(self):
        """
        Override individual request methods (e.g. do_POST) to determine how the
        server will respond to individual requests. You will have to create the
        response, then call _send_header and _send_content.
        """
        response = HTTPResponse(content=["POST response."])
        self._send_header(response.status_code, response.headers)
        self._send_content(response.content)
