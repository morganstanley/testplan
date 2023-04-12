"""HTTPClient Driver."""

import time
import queue
from threading import Thread, Event
from typing import Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import requests
from schema import Use, Or

from testplan.common.config import ConfigOption
from testplan.common.utils.context import expand, is_context, ContextValue
from testplan.common.utils.strings import slugify

from ..base import Driver, DriverConfig


class HTTPClientConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.http.client.HTTPClient`
    driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "host": Or(str, lambda x: is_context(x)),
            ConfigOption("port", default=None): Or(
                None, Use(int), lambda x: is_context(x)
            ),
            ConfigOption("protocol", default="http"): str,
            ConfigOption("timeout", default=5): Use(int),
            ConfigOption("interval", default=0.01): Use(float),
        }


class HTTPClient(Driver):
    """
    Driver for a client that can connect to a server and send/receive messages
    using HTTP protocol.

    {emphasized_members_docs}

    :param name: Name of HTTPClient.
    :type name: ``str``
    :param host: Hostname to connect to.
    :type host: ``str`` or ``ContextValue``
    :param port: Port to connect to. If None URL won't specify a port.
    :type port: ``int`` or ``ContextValue``
    :param protocol: Use HTTP or HTTPS protocol.
    :type protocol: ``str``
    :param timeout: Number of seconds to wait for a request.
    :type timeout: ``int``
    :param interval: Number of seconds to sleep whilst trying to receive a
      message.
    :type interval: ``int``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = HTTPClientConfig

    def __init__(
        self,
        name: str,
        host: Union[str, ContextValue],
        port: Union[int, ContextValue] = None,
        protocol: str = "http",
        timeout: int = 5,
        interval: float = 0.01,
        **options
    ):
        options.update(self.filter_locals(locals()))
        options.setdefault("file_logger", "{}.log".format(slugify(name)))
        super(HTTPClient, self).__init__(**options)
        self._host: str = None
        self._port: Union[int, Literal[""]] = None
        self.protocol = None
        self.timeout = None
        self.interval = None
        self.responses = None
        self.request_threads = []

    @property
    def host(self):
        """Target host name."""
        return self._host

    @property
    def port(self):
        """Client port number assigned."""
        return self._port

    def starting(self):
        """
        Start the HTTPClient.
        """
        super(HTTPClient, self).starting()
        self._host = expand(self.cfg.host, self.context)
        context_port = expand(self.cfg.port, self.context, int)
        self._port = context_port if context_port else ""
        self.protocol = expand(self.cfg.protocol, self.context)
        self.timeout = self.cfg.timeout
        self.interval = self.cfg.interval
        self.responses = queue.Queue()
        port_ = ":{}".format(self.port) if self.port else self.port
        self.logger.info(
            "Started HTTPClient sending requests to %s://%s%s",
            self.protocol,
            self.host,
            port_,
        )

    def stopping(self):
        """
        Stop the HTTPClient.
        """
        super(HTTPClient, self).stopping()

    def aborting(self):
        """Abort logic that stops the client."""
        super(HTTPClient, self).aborting()

    def _send_request(self, method, api, drop_response, timeout, **kwargs):
        """
        Send a request using the requests module.

        :param method: HTTP method to be used in request (e.g. GET, POST etc.).
        :type method: ``str``
        :param api: API to send request to.
        :type api: ``str``
        :param drop_response: Whether to drop the response message (called by
          flush).
        :type drop_response: ``threading._Event``
        :param timeout: Number of seconds to wait for a request.
        :type timeout: ``int``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        http_method = getattr(requests, method, requests.get)
        api = api[1:] if api.startswith("/") else api
        url = "{protocol}://{host}{port}/{api}".format(
            protocol=self.protocol,
            host=self.host,
            port=":{}".format(self.port) if self.port else self.port,
            api=api,
        )
        timeout = kwargs.pop("timeout", timeout)
        self.logger.info(
            "Sending %s request: %s", http_method.__name__.upper(), url
        )
        response = http_method(url=url, timeout=timeout, **kwargs)
        if not drop_response.is_set():
            self.responses.put(response)

    def send(self, method, api, **kwargs):
        """
        Send a non blocking HTTP request.

        :param method: HTTP method to be used in request (e.g. GET, POST etc.).
        :type method: ``str``
        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        drop_response = Event()
        request_thread = Thread(
            target=self._send_request,
            args=(method, api, drop_response, self.timeout),
            kwargs=kwargs,
        )
        request_thread.setDaemon(True)
        request_thread.start()
        self.request_threads.append((request_thread, drop_response))

    def head(self, api, **kwargs):
        """
        Send HEAD request.ZMQClient

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("head", api, **kwargs)

    def get(self, api, params=None, **kwargs):
        """
        Send GET request.

        :param api: API to send request to.
        :type api: ``str``
        :param params: Parameters to append to HTTP request after ?.
        :type params: ``dict``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("get", api, params=params, **kwargs)

    def post(self, api, data=None, json=None, **kwargs):
        """
        Send POST request.

        :param api: API to send request to.
        :type api: ``str``
        :param data: Dictionary to send in the body of the request.
        :type data: ``dict``
        :param json: JSON data to send in the body of the request.
        :type json: ``dict``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("post", api, data=data, json=json, **kwargs)

    def put(self, api, data=None, **kwargs):
        """
        Send PUT request.

        :param api: API to send request to.
        :type api: ``str``
        :param data: Dictionary to send in the body of the request.
        :type data: ``dict``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("put", api, data=data, **kwargs)

    def delete(self, api, **kwargs):
        """
        Send DELETE request.

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("delete", api, **kwargs)

    def patch(self, api, data=None, **kwargs):
        """
        Send PATCH request.

        :param api: API to send request to.
        :type api: ``str``
        :param data: Dictionary to send in the body of the request.
        :type data: ``dict``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("patch", api, data=data, **kwargs)

    def options(self, api, **kwargs):
        """
        Send OPTIONS request.

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send("options", api, **kwargs)

    def receive(self, timeout=None):
        """
        Wait to receive a response.

        :param timeout: Number of seconds to wait for a response,
          overrides timeout from init.
        :type timeout: ``int``

        :return: A request response or ``None``
        :rtype: ``requests.models.Response`` or ``NoneType``
        """
        timeout = timeout if timeout is not None else self.timeout
        timeout += time.time()
        response = None

        while time.time() < timeout:
            try:
                response = self.responses.get(False)
            except queue.Empty:
                self.logger.debug("Waiting for response...")
                response = None
            else:
                self.responses.task_done()
                self.logger.info("Received response.")
                break
            time.sleep(self.interval)

        return response

    def flush(self):
        """
        Drop any currently incoming messages and flush the received messages
        queue.
        """
        for _, drop_message in self.request_threads:
            drop_message.set()
            self.logger.debug("Request thread set to drop response.")

        timeout = time.time() + (5 * self.timeout)
        while not self.responses.empty() and time.time() < timeout:
            try:
                self.responses.get(block=False)
            except queue.Empty:
                self.logger.debug("Responses queue flushed.")
            else:
                self.responses.task_done()
