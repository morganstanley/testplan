"""HTTPClient Driver."""

from schema import Use, Or
from threading import Thread, Event
import time
import os
try:
  import Queue
except ImportError:
  import queue as Queue

import requests

from testplan.common.config import ConfigOption as Optional
from testplan.common.utils.context import expand, is_context
from testplan.common.utils.strings import slugify

from ..base import Driver, DriverConfig


class HTTPClientConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.http.client.HTTPClient` driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            'host': Or(str, lambda x: is_context(x)),
            Optional('port', default=None): Or(None, Use(int),
                                               lambda x: is_context(x)),
            Optional('protocol', default='http'): str,
            Optional('timeout', default=5): Use(int),
            Optional('interval', default=0.01): Use(float)
        }


class HTTPClient(Driver):
    """
    HTTPClient driver.

    :param host: Hostname to connect to.
    :type host: ``str`` or ``ContextValue``
    :param port: Port to connect to. If None URL won't specify a port.
    :type port: ``str`` or ``ContextValue``
    :param protocol: Use HTTP or HTTPS protocol.
    :type protocol: ``str``
    :param timeout: Number of seconds to wait for a request.
    :type timeout: ``int``
    :param interval: Number of seconds to sleep whilst trying to receive a
      message.
    :type interval: ``int``
    """

    CONFIG = HTTPClientConfig

    def __init__(self, **options):
        super(HTTPClient, self).__init__(**options)
        self._host = None
        self._port = None
        self.protocol = None
        self.timeout = None
        self.interval = None
        self.responses = None
        self.request_threads = []
        self._logname = '{0}.log'.format(slugify(self.cfg.name))

    @property
    def logpath(self):
        """HTTPClient logfile in runpath."""
        return os.path.join(self.runpath, self._logname)

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
        self._setup_file_logger(self.logpath)
        self._host = expand(self.cfg.host, self.context)
        context_port = expand(self.cfg.port, self.context, int)
        self._port = context_port if context_port else ''
        self.protocol = expand(self.cfg.protocol, self.context)
        self.timeout = self.cfg.timeout
        self.interval = self.cfg.interval
        self.responses = Queue.Queue()
        self.file_logger.debug(
            'Started HTTPClient sending requests to {}://{}{}'.format(
                self.protocol,
                self.host,
                ':{}'.format(self.port) if self.port else self.port
            )
        )

    def stopping(self):
        """
        Stop the HTTPClient.
        """
        super(HTTPClient, self).stopping()
        self.file_logger.debug('Stopped HTTPClient.')

    def aborting(self):
        """Abort logic that stops the client."""
        self.file_logger.debug('Aborting HTTPClient.')

    def _send_request(self, method, api, drop_response, timeout, **kwargs):
        """
        Send a request using the requests module.

        :param method: HTTP method to be used in request (e.g. GET, POST etc.).
        :type method: ``str``
        :param api: API to send request to.
        :type api: ``str``
        :param drop_response: Whether to drop the response message (called by flush).
        :type drop_response: ``threading._Event``
        :param timeout: Number of seconds to wait for a request.
        :type timeout: ``int``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        http_method = getattr(requests, method, requests.get)
        api = api[1:] if api.startswith('/') else api
        url = '{protocol}://{host}{port}/{api}'.format(
            protocol=self.protocol,
            host=self.host,
            port=':{}'.format(self.port) if self.port else self.port,
            api=api
        )
        timeout = kwargs.pop('timeout', timeout)
        self.file_logger.debug('Sending {} request: {}'.format(
            http_method.__name__.upper(),
            url
        ))
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
            kwargs=kwargs
        )
        request_thread.setDaemon(True)
        request_thread.start()
        self.request_threads.append((request_thread, drop_response))

    def head(self, api, **kwargs):
        """
        Send HEAD request.

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
        modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send('head', api, **kwargs)

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
        self.send('get', api, params=params, **kwargs)

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
        self.send('post', api, data=data, json=json, **kwargs)

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
        self.send('put', api, data=data, **kwargs)

    def delete(self, api, **kwargs):
        """
        Send DELETE request.

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send('delete', api, **kwargs)

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
        self.send('patch', api, data=data, **kwargs)

    def options(self, api, **kwargs):
        """
        Send OPTIONS request.

        :param api: API to send request to.
        :type api: ``str``
        :param kwargs: Optional arguments for the request, look at the requests
          modules docs for these arguments.
        :type kwargs: Depends on the argument.
        """
        self.send('options', api, **kwargs)

    def receive(self, timeout=None):
        """
        Wait to receive a response.

        :param timeout: Number of seconds to wait for a response,
          overrides timeout from init.
        :type timeout: ``int``

        :return: A request response or ``None``
        :rtype: ``requests.models.Response`` or ``NoneType``
        """
        timeout = time.time() + (timeout or self.timeout)
        while time.time() < timeout:
            try:
                response = self.responses.get(False)
            except Queue.Empty:
                self.file_logger.debug('Waiting for response...')
                response = None
            else:
                self.responses.task_done()
                self.file_logger.debug('Received response.')
                break
            time.sleep(self.interval)
        return response

    def flush(self):
        """Drop any currently incoming messages and flush the received messages queue."""
        for _, drop_message in self.request_threads:
            drop_message.set()
            self.file_logger.debug('Request thread set to drop response.')

        timeout = time.time() + (5 * self.timeout)
        while not self.responses.empty() and time.time() < timeout:
            try:
                self.responses.get(block=False)
            except Queue.Empty:
                self.file_logger.debug('Responses queue flushed.')
            else:
                self.responses.task_done()
