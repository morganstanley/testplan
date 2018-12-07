"""HTTPServer Driver."""

from schema import Use, Or
from threading import Thread
import time
import os
try:
  import BaseHTTPServer as http_server
  import Queue as queue
except ImportError:
  import http.server as http_server
  import queue


from testplan.common.config import ConfigOption as Optional
from testplan.common.utils.strings import slugify

from ..base import Driver, DriverConfig


class HTTPRequestHandler(http_server.BaseHTTPRequestHandler):
    """
    Responds to any HTTP request with response in queue. If empty send an error
    message in response.
    """
    def _send_header(self, status_code=200, headers=None):
        """
        Send a header response.

        :param status_code: The returned status code.
        :type status_code: ``int``
        :param headers: The returned headers.
        :type headers: ``dict``

        :return: ``None``
        :rtype: ``NoneType``
        """
        if headers is None:
            headers = {'Content-type': 'text/plain'}
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
                line = line.encode('utf-8')
            except AttributeError:
                pass
            self.wfile.write(line)

    def _parse_request(self):
        """
        Put the request into the HTTPServer's requests queue. Get the response
        from the HTTPServer's response queue. If there is no response send an
        error message back.

        :return: ``None``
        :rtype: ``NoneType``
        """
        response = self.get_response(request=self.path)
        if not isinstance(response, HTTPResponse):
            raise TypeError('Response must be of type HTTPResponse')

        self._send_header(status_code=response.status_code,
                         headers=response.headers)
        self._send_content(response.content)
        self.server.log_callback(
            'Sent response with:\n  status code {}\n  headers {}'.format(
                response.status_code,
                response.headers
            )
        )

    def log_message(self, format, *args):
        """Log messages from the BaseHTTPRequestHandler class."""
        self.server.log_callback('BASE CLASS: {}'.format(format%args))

    def get_response(self, request):
        """
        Parse the request and return the response.

        :param request:
        :return:
        """
        self.server.requests.put(request)

        timeout = time.time() + self.server.timeout
        while time.time() < timeout:
            try:
                response = self.server.responses.get(False)
            except queue.Empty:
                response = HTTPResponse(
                    status_code=500,
                    content=['No response in driver queue.']
                )
                self.server.log_callback(
                    'No response found in queue.'
                )
            else:
                self.server.log_callback('Response popped from queue.')
                break
            time.sleep(self.server.interval)
        if response.status_code == 500:
            self.server.log_callback('Responding with 500 error.')
        return response

    def do_HEAD(self):
        """Handles a HEAD request."""
        self._send_header()
        self.server.log_callback('Sending response to HEAD request.')

    def do_GET(self):
        """Handles a GET request."""
        self._parse_request()
        self.server.log_callback('Sending response to GET request.')

    def do_POST(self):
        """Handles a POST request."""
        self._parse_request()
        self.server.log_callback('Sending response to POST request.')

    def do_PUT(self):
        """Handles a PUT request."""
        self._parse_request()
        self.server.log_callback('Sending response to PUT request.')

    def do_DELETE(self):
        """Handles a DELETE request."""
        self._parse_request()
        self.server.log_callback('Sending response to DELETE request.')

    def do_PATCH(self):
        """Handles a PATCH request."""
        self._parse_request()
        self.server.log_callback('Sending response to PATCH request.')

    def do_OPTIONS(self):
        """Handles a OPTIONS request."""
        self._parse_request()
        self.server.log_callback('Sending response to OPTIONS request.')


class HTTPServerConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.http.server.HTTPServer` driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            Optional('host', default='localhost'): str,
            Optional('port', default=0): Use(int),
            Optional('request_handler', default=HTTPRequestHandler):
                lambda v: issubclass(v, http_server.BaseHTTPRequestHandler),
            Optional('handler_attributes', default={}): dict,
            Optional('timeout', default=5): Use(int),
            Optional('interval', default=0.01): Use(float)
        }


class HTTPServer(Driver):
    """
    Driver for a server that can send and receive messages over the HTTP
    protocol.

    :param name: Name of the driver.
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
    """

    CONFIG = HTTPServerConfig

    def __init__(self, **options):
        super(HTTPServer, self).__init__(**options)
        self._host = None
        self._port = None
        self.request_handler = None
        self.handler_attributes = None
        self.timeout = None
        self.interval = None
        self.requests = None
        self.responses = None
        self._server_thread = None
        self._logname = '{0}.log'.format(slugify(self.cfg.name))

    @property
    def logpath(self):
        """HTTPServer logfile in runpath."""
        return os.path.join(self.runpath, self._logname)

    @property
    def host(self):
        """Host name."""
        return self._host

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
            raise TypeError('Response must be of type HTTPResponse')
        self.responses.put(response)
        self.file_logger.debug('Added response to HTTPServer response queue.')

    def respond(self, response):
        """
        Put an HTTPResponse on to the end of the response queue.

        :param response: A response to be sent.
        :type response: ``HTTPResponse``
        """
        self.queue_response(response)

    def get_request(self):
        """
        Get a request sent to the HTTPServer, if the requests queue is empty
        return None.

        :return: A request from the queue or ``None``
        :rtype: ``str`` or ``NoneType``
        """
        try:
            return self.requests.get(False)
        except queue.Empty:
            return None

    def starting(self):
        """Start the HTTPServer."""
        super(HTTPServer, self).starting()
        self._setup_file_logger(self.logpath)
        self.request_handler = self.cfg.request_handler
        self.handler_attributes = self.cfg.handler_attributes
        self.timeout = self.cfg.timeout
        self.interval = self.cfg.interval
        self.requests = queue.Queue()
        self.responses = queue.Queue()

        self._server_thread = _HTTPServerThread(host=self.cfg.host,
                                                port=self.cfg.port,
                                                requests_queue=self.requests,
                                                responses_queue=self.responses,
                                                handler_attributes=self.handler_attributes,
                                                request_handler=self.request_handler,
                                                timeout=self.timeout,
                                                logger=self.file_logger)
        self._server_thread.setName(self.name)
        self._server_thread.start()

        while not hasattr(self._server_thread.server, 'server_port'):
            time.sleep(0.1)
        self._host, self._port = self._server_thread.server.server_address
        self.file_logger.debug(
            'Started HTTPServer listening on http://{host}:{port}'.format(
                host=self.host,
                port=self.port
            )
        )

    def _stop(self):
        """Stop the HTTPServer."""
        if self._server_thread:
            self._server_thread.stop()

    def stopping(self):
        """Stop the HTTPServer."""
        super(HTTPServer, self).stopping()
        self._stop()
        self.file_logger.debug('Stopped HTTPServer.')

    def aborting(self):
        """Abort logic that stops the server."""
        self._stop()
        self.file_logger.debug('Aborted HTTPServer.')


class HTTPResponse(object):
    """
    HTTPResponse containing the status code, headers and content.

    :param status_code: The returned status code.
    :type status_code: ``int``
    :param headers: A dictionary containing the header keywords and values.
    :type headers: ``dict``
    :param content: A list of strings to be sent back.
    :type content: ``list``
    """
    def __init__(self, status_code=None, headers=None, content=None):
        self.status_code = status_code or 200
        self.headers = headers or {'Content-type': 'text/plain'}
        self.content = content or []


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
    def __init__(self, host, port, requests_queue, responses_queue,
                 handler_attributes, request_handler=None, timeout=5,
                 interval=0.01, logger=None):
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
          RequestHandlerClass=self.request_handler
        )
        self.server.requests = self.requests_queue
        self.server.responses = self.responses_queue
        self.server.handler_attributes = self.handler_attributes
        self.server.timeout = self.timeout
        self.server.interval = self.interval
        nothing = lambda msg: None
        self.server.log_callback = self.logger.debug if self.logger else nothing
        self.server.serve_forever()

    def stop(self):
        """Stop the HTTP server thread."""
        if self.server is not None:
          self.server.shutdown()
