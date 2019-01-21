"""
Http handler for interactive mode.
"""

import json
import six
import uuid
import inspect
import threading

if six.PY2:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SocketServer import ThreadingMixIn
    from urlparse import urlparse, parse_qs
else:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
    from urllib.parse import urlparse, parse_qs

from testplan.common.utils.exceptions import format_trace
from testplan.common.config import ConfigOption
from testplan.common.entity import Entity, EntityConfig


class TestRunnerHTTPHandlerConfig(EntityConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.http.TestRunnerHTTPHandler` entity.
    """
    @classmethod
    def get_options(cls):
        return {'ihandler' : object,
                ConfigOption('host', default='localhost'): object,
                ConfigOption('port', default=0): int}


class TestRunnerHTTPHandler(Entity):
    """
    Server that invokes an interactive handler to perform dynamic operations.

    :param ihandler: Runnable interactive handler instance.
    :type ihandler: Subclass of
      :py:class:`RunnableIHandler <testplan.common.entity.base.RunnableIHandler>`
    :param host: Host to bind to.
    :type host: ``str``
    :param port: Port to bind to.
    :type port: ``int``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Entity` options.
    """
    CONFIG = TestRunnerHTTPHandlerConfig

    def __init__(self, **options):
        super(TestRunnerHTTPHandler, self).__init__(**options)
        self._ip = None
        self._port = None

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def run(self):
        """
        Runs the threader HTTP handler for interactive mode.
        """
        outer = self

        class Handler(BaseHTTPRequestHandler):
            MODES = set(['sync', 'async', 'async_result'])
            LOCK = threading.Lock()
            EXEC_STATE = {}
            RESULTS = {}

            def sync(self, method, **kwargs):
                """Perform a synchronous operation."""
                outer.logger.debug('Calling {}(**{})'.format(method, kwargs))
                with self.LOCK:
                    return getattr(outer.cfg.ihandler, method)(**kwargs)

            def async(self, method, **kwargs):
                """Perform an asynchronous operation."""
                uid = str(uuid.uuid4())
                thread = threading.Thread(
                    target=self._execute_in_thread, args=(uid, method, kwargs))
                thread.daemon = True
                thread.start()
                self.EXEC_STATE[uid] = 'Scheduled'
                return uid

            def _execute_in_thread(self, uid, method, kwargs):
                try:
                    with self.LOCK:
                        self.EXEC_STATE[uid] = 'Executing'
                        result = getattr(outer.cfg.ihandler, method)(**kwargs)
                        self.EXEC_STATE[uid] = 'Finished'
                except Exception as exc:
                    result = exc
                self.RESULTS[uid] = result

            def _make_response(self, message, response=None,
                         error=False, trace=None, result=None, **metadata):
                response = response or {}
                response.update(
                    {'message': message, 'result': result,
                     'error': error, 'trace': trace,
                     'metadata': metadata})
                return response

            def _async_result(self, uid):
                if uid not in self.EXEC_STATE:
                    response = self._make_response(
                        error=True,
                        message='{} not recognised.'.format(uid))
                    self.send_response(404)
                elif uid not in self.RESULTS:
                    response = self._make_response(
                        error=True,
                        message='{} not finished.'.format(uid),
                        state=self.EXEC_STATE[uid])
                    self.send_response(404)
                else:
                    self.send_response(200)
                    response = self._make_response(
                        message='{} finished.'.format(uid),
                        result=self.RESULTS[uid],
                        state=self.EXEC_STATE[uid])
                    del self.EXEC_STATE[uid]
                    del self.RESULTS[uid]
                return response

            def _header_json(self, code=200):
                """
                Sets the next message's context type as text/json
                """
                self.send_response(code)
                self.send_header('Content-type', 'text/json')
                self.end_headers()

            def _write_json(self, response):
                return self.wfile.write(response)

            def _extract_mode_method(self, path):
                if path.count('/') == 1:
                    return path.split('/')[1], None
                elif path.count('/') == 2:
                    return path.split('/')[1], path.split('/')[2]
                else:
                    raise ValueError('Incorrent path: {}'.format(path))

            def do_POST(self):
                """
                Handle post requests.
                """
                response = {}
                outer.logger.debug('path: {}'.format(self.path))
                url = urlparse(self.path)
                outer.logger.debug('url: {}'.format(url))
                query_params = parse_qs(url.query)
                outer.logger.debug('query params: {}'.format(query_params))

                try:
                    length = int(self.headers.getheader('content-length'))
                    request = json.loads(self.rfile.read(length))
                    mode, method = self._extract_mode_method(self.path)
                    if mode not in self.MODES:
                        raise ValueError('Execution {} not valid: {}'.format(
                            mode, self.MODES))
                    if mode == 'sync':
                        response['result'] = self.sync(method, **request)
                    elif mode == 'async':
                        response['result'] = self.async(method, **request)
                    elif mode == 'async_result':
                        response = self._async_result(**request)
                    self._header_json()
                except Exception as exc:
                    msg = '{} exception in do_POST: {}'.format(
                        outer.__class__.__name__, exc)
                    outer.logger.critical(msg)
                    response = self._make_response(
                        message=msg,
                        error=True,
                        trace=format_trace(inspect.trace()))
                    self._header_json(code=400)
                self._write_json(response)

        class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
            """Handle requests in a separate thread."""

        server = ThreadedHTTPServer((self.cfg.host, self.cfg.port), Handler)
        self._ip, self._port = server.server_address
        server.serve_forever()
