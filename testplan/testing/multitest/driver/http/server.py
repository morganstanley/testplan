"""HTTPServer Driver."""

import time
import queue
import json
import http.server as http_server
from threading import Thread
from typing import Optional

from schema import Use

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.strings import slugify

from ..base import Driver, DriverConfig

_CONTENT_TYPE_KEY = "Content-Type"
_CONTENT_LENGTH_KEY = "Content-Length"


class ReceivedRequest:
    """
    Stores information of requests received by the HTTP Server.
    """

    def __init__(
        self,
        method: str,
        path_url: str,
        headers: dict,
        raw_data: bytes,
        raw_requestline: bytes,
        requestline: str,
        request_version: str,
    ) -> None:
        """
        Constructs a new received request

        :param method: method of the request, eg.: GET, POST, HEAD...
        :param path_url: URL of the request
        :param headers: Dictionary of HTTP Headers sent with the request
        :param raw_data: Data sent in the body of the request in original bytes format
        :param raw_requestline: The first line of the request containing
            the method, URL and version in original bytes format
        :param requestline: The first line of the request containing
            the method, URL and version in string format
        :param request_version: Human-readable string of the protocol version
        """

        # Default empty dict for headers.
        headers = {} if headers is None else headers

        self.method = method
        self.path_url = path_url
        self.headers = headers
        self.raw_data = raw_data
        self.raw_requestline = raw_requestline
        self.requestline = requestline
        self.request_version = request_version

    def __str__(self) -> str:
        """
        String representation of the first line of the request.
        """
        return self.requestline

    @property
    def content_type(self) -> Optional[str]:
        """
        Returns the request's content type

        :return Content type header or None
        """
        if _CONTENT_TYPE_KEY in self.headers:
            return self.headers[_CONTENT_TYPE_KEY]
        else:
            return None

    @property
    def json(self) -> Optional[dict]:
        """
        Returns the request's data in JSON format if exists

        :return Request's data in JSON format or None
        """
        if (
            self.raw_data is not None
            and self.content_type == "application/json"
        ):
            return json.loads(self.raw_data)
        else:
            return None


class HTTPResponse:
    """
    HTTPResponse containing the status code, headers and content.
    """

    def __init__(
        self,
        status_code: int = None,
        headers: dict = None,
        content: list = None,
    ) -> None:
        """
        Constructs a HTTPResponse

        :param status_code: The returned status code.
        :param headers: A dictionary containing the header keywords and values.
        :param content: A list of strings to be sent back.
        """
        self.status_code = status_code or 200
        self.headers = headers or {_CONTENT_TYPE_KEY: "text/plain"}
        self.content = content or []


class HTTPRequestHandler(http_server.BaseHTTPRequestHandler):
    """
    Responds to any HTTP request with response in queue. If empty send an error
    message in response.
    """

    def _send_header(
        self, status_code: int = 200, headers: dict = None
    ) -> None:
        """
        Send a header response.

        :param status_code: The returned status code.
        :param headers: The returned headers.
        """
        if headers is None:
            headers = {_CONTENT_TYPE_KEY: "text/plain"}
        self.send_response(code=int(status_code))
        for keyword, value in headers.items():
            self.send_header(keyword, value)
        self.end_headers()

    def _send_content(self, content):
        """
        Send the content response.

        :param content: A list of strings to be sent back.
        :type content: ``list``
        """
        for line in content:
            try:
                line = line.encode("utf-8")
            except AttributeError:
                pass
            self.wfile.write(line)

    def _parse_request(self) -> None:
        """
        Put the request into the HTTPServer's requests queue. Get the response
        from the HTTPServer's response queue. If there is no response send an
        error message back.
        """
        raw_content = None

        if _CONTENT_LENGTH_KEY in self.headers:
            raw_content = self.rfile.read(
                int(self.headers[_CONTENT_LENGTH_KEY])
            )

        response = self.get_response(
            ReceivedRequest(
                headers=self.headers,
                path_url=self.path,
                raw_data=raw_content,
                raw_requestline=self.raw_requestline,
                requestline=self.requestline,
                method=self.command,
                request_version=self.request_version,
            )
        )

        if not isinstance(response, HTTPResponse):
            raise TypeError("Response must be of type HTTPResponse")

        self._send_header(
            status_code=response.status_code, headers=response.headers
        )
        self._send_content(response.content)
        self.server.log_callback(
            "Sent response with:\n  status code {}\n  headers {}".format(
                response.status_code, response.headers
            )
        )

    def log_message(self, format, *args):
        """Log messages from the BaseHTTPRequestHandler class."""
        self.server.log_callback("BASE CLASS: {}".format(format % args))

    def get_response(self, request: ReceivedRequest) -> HTTPResponse:
        """
        Parse the request and return the response.

        :param request: The request path.
        :return: Http response.
        """
        self.server.requests.put(request)

        timeout = time.time() + self.server.timeout
        while time.time() < timeout:
            try:
                response = self.server.responses.get(False)
            except queue.Empty:
                response = HTTPResponse(
                    status_code=500, content=["No response in driver queue."]
                )
                self.server.log_callback("No response found in queue.")
            else:
                self.server.log_callback("Response popped from queue.")
                break
            time.sleep(self.server.interval)
        if response.status_code == 500:
            self.server.log_callback("Responding with 500 error.")
        return response

    def do_HEAD(self):
        """Handles a HEAD request."""
        self._send_header()
        self.server.log_callback("Sending response to HEAD request.")

    def do_GET(self):
        """Handles a GET request."""
        self._parse_request()
        self.server.log_callback("Sending response to GET request.")

    def do_POST(self):
        """Handles a POST request."""
        self._parse_request()
        self.server.log_callback("Sending response to POST request.")

    def do_PUT(self):
        """Handles a PUT request."""
        self._parse_request()
        self.server.log_callback("Sending response to PUT request.")

    def do_DELETE(self):
        """Handles a DELETE request."""
        self._parse_request()
        self.server.log_callback("Sending response to DELETE request.")

    def do_PATCH(self):
        """Handles a PATCH request."""
        self._parse_request()
        self.server.log_callback("Sending response to PATCH request.")

    def do_OPTIONS(self):
        """Handles a OPTIONS request."""
        self._parse_request()
        self.server.log_callback("Sending response to OPTIONS request.")


class HTTPServerConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.http.server.HTTPServer`
    driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption("host", default="localhost"): str,
            ConfigOption("port", default=0): Use(int),
            ConfigOption(
                "request_handler", default=HTTPRequestHandler
            ): lambda v: issubclass(v, http_server.BaseHTTPRequestHandler),
            ConfigOption("handler_attributes", default={}): dict,
            ConfigOption("timeout", default=5): Use(int),
            ConfigOption("interval", default=0.01): Use(float),
        }


class HTTPServer(Driver):
    """
    Driver for a server that can accept connection and send/receive messages
    using HTTP protocol.

    {emphasized_members_docs}

    :param name: Name of HTTPServer.
    :type name: ``str``
    :param host: Hostname to connect to.
    :type host: ``str`` or ``ContextValue``
    :param port: Port to connect to.
    :type port: ``str`` or ``ContextValue``
    :param request_handler: Handles requests and responses for the server.
    :type request_handler: subclass of ``http.server.BaseHTTPRequestHandler``
    :param handler_attributes: Dictionary of attributes to be accessed from the
      request_handler.
    :type handler_attributes: ``dict``
    :param timeout: Number of seconds to wait for a response from the queue in
      the request_handler.
    :type timeout: ``int``
    :param interval: Time to wait between each attempt to get a response.
    :type interval: ``int``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = HTTPServerConfig

    def __init__(
        self,
        name,
        host: str = "localhost",
        port: int = 0,
        request_handler=HTTPRequestHandler,
        handler_attributes=None,
        timeout=5,
        interval=0.01,
        **options
    ):
        options.update(self.filter_locals(locals()))
        options.setdefault("file_logger", "{}.log".format(slugify(name)))
        super(HTTPServer, self).__init__(**options)
        self._host: str = None
        self._port: int = None
        self.request_handler = None
        self.handler_attributes = None
        self.timeout = None
        self.interval = None
        self.requests = None
        self.responses = None
        self._server_thread = None

    @emphasized
    @property
    def host(self):
        """Host name."""
        return self._host

    @emphasized
    @property
    def port(self):
        """Port number assigned."""
        return self._port

    def queue_response(self, response):
        """
        Put an HTTPResponse on to the end of the response queue.

        :param response: A response to be sent.
        :type response: ``HTTPResponse``
        """
        if not isinstance(response, HTTPResponse):
            raise TypeError("Response must be of type HTTPResponse")
        self.responses.put(response)
        self.logger.debug("Added response to HTTPServer response queue.")

    def respond(self, response):
        """
        Put an HTTPResponse on to the end of the response queue.

        :param response: A response to be sent.
        :type response: ``HTTPResponse``
        """
        self.queue_response(response)

    def get_request(self) -> Optional[str]:
        """
        Get a request sent to the HTTPServer, if the requests queue is empty
        return None.

        :return: A request from the queue or ``None``
        """
        try:
            return self.requests.get(False).path_url
        except queue.Empty:
            return None

    def get_full_request(self) -> Optional[ReceivedRequest]:
        """
        Get a request sent to the HTTPServer, if the requests queue is empty
        return None.

        :return: A request from the queue or ``None``
        """
        try:
            return self.requests.get(False)
        except queue.Empty:
            return None

    def receive(self, timeout: int = None) -> Optional[ReceivedRequest]:
        """
        Wait to receive a request.

        :param timeout: Number of seconds to wait for a request,
          overrides timeout from init.
        :return: A request or ``None``
        """
        timeout = timeout if timeout is not None else self.timeout
        timeout += time.time()
        request = None

        while time.time() < timeout:
            try:
                request = self.requests.get(False)
            except queue.Empty:
                self.logger.debug("Waiting for request...")
                request = None
            else:
                self.requests.task_done()
                self.logger.debug("Received request.")
                break
            time.sleep(self.interval)

        return request

    def starting(self):
        """Start the HTTPServer."""
        super(HTTPServer, self).starting()
        self.request_handler = self.cfg.request_handler
        self.handler_attributes = self.cfg.handler_attributes
        self.timeout = self.cfg.timeout
        self.interval = self.cfg.interval
        self.requests = queue.Queue()
        self.responses = queue.Queue()

        self._server_thread = _HTTPServerThread(
            host=self.cfg.host,
            port=self.cfg.port,
            requests_queue=self.requests,
            responses_queue=self.responses,
            handler_attributes=self.handler_attributes,
            request_handler=self.request_handler,
            timeout=self.timeout,
            logger=self.logger,
        )
        self._server_thread.setName(self.name)
        self._server_thread.start()

        while not hasattr(self._server_thread.server, "server_port"):
            time.sleep(0.1)
        self._host, self._port = self._server_thread.server.server_address
        self.logger.info(
            "Started HTTPServer listening on http://%s:%s",
            self.host,
            self.port,
        )

    def _stop(self):
        """Stop the HTTPServer."""
        if self._server_thread:
            self._server_thread.stop()

    def stopping(self):
        """Stop the HTTPServer."""
        super(HTTPServer, self).stopping()
        self._stop()

    def aborting(self):
        """Abort logic that stops the server."""
        super(HTTPServer, self).aborting()
        self._stop()

    def flush_request_queue(self) -> None:
        """Flush the received messages queue."""
        timeout = time.time() + (5 * self.timeout)
        while not self.requests.empty() and time.time() < timeout:
            try:
                self.requests.get(block=False)
            except queue.Empty:
                self.logger.debug("Requests queue flushed.")
            else:
                self.requests.task_done()


class _HTTPServerThread(Thread):
    """
    HTTP server running on a separate thread.

    :param host: Host address for HTTP server.
    :type host: ``str``
    :param port: Port for HTTP server.
    :type port: ``int``
    :param requests_queue: Requests queue for HTTP server.
    :type requests_queue: ``Queue.Queue``
    :param responses_queue: Responses queue for HTTP server.
    :type responses_queue: ``Queue.Queue``
    :param handler_attributes: Dictionary of attributes to be accessed from the
      request_handler.
    :type handler_attributes: ``dict``
    :param request_handler: Handles requests and responses for the server.
    :type request_handler: subclass of ``http.server.BaseHTTPRequestHandler``
    :param timeout: Number of seconds to wait for a response from the queue in
      the request_handler.
    :param interval: Time to wait between each attempt to get a response.
    :type interval: ``int``
    :type timeout: ``int``
    :param logger: Logger for the driver.
    :type logger: ``logging.Logger``
    """

    def __init__(
        self,
        host,
        port,
        requests_queue,
        responses_queue,
        handler_attributes,
        request_handler=None,
        timeout=5,
        interval=0.01,
        logger=None,
    ):
        super(_HTTPServerThread, self).__init__()
        self.host = host
        self.port = port
        self.requests_queue = requests_queue
        self.responses_queue = responses_queue
        self.handler_attributes = handler_attributes
        self.request_handler = request_handler or HTTPRequestHandler
        self.timeout = timeout
        self.interval = interval
        self.logger = logger
        self.server = None

    def run(self):
        """Start the HTTP server thread."""
        self.server = http_server.HTTPServer(
            server_address=(self.host, self.port),
            RequestHandlerClass=self.request_handler,
        )
        self.server.requests = self.requests_queue
        self.server.responses = self.responses_queue
        self.server.handler_attributes = self.handler_attributes
        self.server.timeout = self.timeout
        self.server.interval = self.interval
        nothing = lambda msg: None
        self.server.log_callback = (
            self.logger.debug if self.logger else nothing
        )
        self.server.serve_forever()

    def stop(self):
        """Stop the HTTP server thread."""
        if self.server is not None:
            self.server.shutdown()
