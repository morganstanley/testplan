"""FixClient driver classes."""

import os
import errno
import socket

from schema import Use, Or

from testplan.common.config import ConfigOption
from testplan.common.utils.context import is_context, expand
from testplan.common.utils.strings import slugify
from testplan.common.utils.sockets.fix.client import Client
from testplan.common.utils.timing import (TimeoutException,
                                          TimeoutExceptionInfo)

from ..base import Driver, DriverConfig


class FixClientConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.fix.client.FixClient` driver.
    """

    @classmethod
    def get_options(cls):
        return {
            'msgclass': type,
            'codec': object,
            'host': Or(str,
                       lambda x: is_context(x)),
            'port': Or(Use(int), lambda x: is_context(x)),
            'sender': str,
            'target': str,
            ConfigOption('version', default='FIX.4.2'): str,
            ConfigOption('sendersub', default=None): str,
            ConfigOption('interface', default=None): tuple,
            ConfigOption('connect_at_start', default=True): bool,
            ConfigOption('logon_at_start', default=True): bool,
            ConfigOption('custom_logon_tags', default=None): object,
            ConfigOption('receive_timeout', default=30):
                Or(int, float),
            ConfigOption('logon_timeout', default=10):
                Or(int, float),
            ConfigOption('logoff_timeout', default=3):
                Or(int, float)
        }


class FixClient(Driver):
    """
    Fix client driver.

    This is built on top of the
    :py:class:`testplan.common.utils.sockets.fix.client.Client` class, which
    provides equivalent functionality and may be used outside of MultiTest.

    :param msgclass: Type used to construct logon, logoff and received FIX
          messages.
    :type msgclass: ``type``
    :param codec: A Codec to use to encode and decode FIX messages.
    :type codec: a ``Codec`` instance
    :param host: Target host name. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type host: ``str``
    :param port: Target port number. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type port: ``int``
    :param sender: FIX SenderCompID.
    :type sender: ``str``
    :param target: FIX TargetCompID.
    :type target: ``str``
    :param version: FIX version, defaults to "FIX.4.2".
    :type version: ``str``
    :param sendersub: FIX SenderSubID.
    :type sendersub: ``str``
    :param interface: Interface to bind to.
    :type interface: ``tuple``(``str, ``int``)
    :param connect_at_start: Connect to server on start. Default: True
    :type connect_at_start: ``bool``
    :param logon_at_start: Attempt FIX logon if connected at start.
    :type logon_at_start: ``bool``
    :param custom_logon_tags: Custom logon tags to be merged into
      the ``35=A`` message.
    :type custom_logon_tags: ``FixMessage``
    :param logon_timeout: Timeout in seconds while receiving from socket.
    :type logon_timeout: ``int`` or ``float``
    :param logon_timeout: Timeout in seconds to wait for logon response.
    :type logon_timeout: ``int`` or ``float``
    :param logoff_timeout: Timeout in seconds to wait for logoff response.
    :type logoff_timeout: ``int`` or ``float``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver`` options.
    """

    CONFIG = FixClientConfig

    def __init__(self, **options):
        super(FixClient, self).__init__(**options)
        self._host = None
        self._port = None
        self._client = None
        self._logname = '{0}.log'.format(slugify(self.cfg.name))

    @property
    def logpath(self):
        """Fix client logfile in runpath."""
        return os.path.join(self.runpath, self._logname)

    @property
    def host(self):
        """Target host name."""
        return self._host

    @property
    def port(self):
        """Client port number assigned."""
        return self._port

    @property
    def sender(self):
        """Shortcut to be used inside testcases."""
        return self.cfg.sender

    @property
    def target(self):
        """Shortcut to be used inside testcases."""
        return self.cfg.target

    @property
    def sendersub(self):
        """Shortcut to be used inside testcases."""
        return self.cfg.sendersub

    def starting(self):
        """Start the FIX client and optionally connect to host/post."""
        super(FixClient, self).starting()
        self._setup_file_logger(self.logpath)
        self.reconnect()

    def connect(self):
        """
        Connect client.
        """
        self._client.connect()
        self._host, self._port = self._client.address

    def reconnect(self):
        """
        Starts a stopped FixClient instance reconnecting to the original host
        and port as it was originally started with.

        If host and port were specified as context values they will be resolved
        again at this point.

        This is helpful in cases the dependent process has also restarted on a
        different port.
        """
        self._stop_logic()
        server_host = expand(self.cfg.host, self.context)
        server_port = expand(self.cfg.port, self.context, int)

        self._client = Client(msgclass=self.cfg.msgclass, codec=self.cfg.codec,
                              host=server_host, port=server_port,
                              sender=self.cfg.sender, target=self.cfg.target,
                              version=self.cfg.version,
                              sendersub=self.cfg.sendersub,
                              interface=self.cfg.interface,
                              logger=self.file_logger)

        if self.cfg.connect_at_start or self.cfg.logon_at_start:
            self.connect()
        if self.cfg.logon_at_start:
            self.logon()

    def logon(self):
        """
        Logon to server.
        """
        self._client.sendlogon(custom_tags=self.cfg.custom_logon_tags)
        rcv = self._client.receive(timeout=self.cfg.logon_timeout)
        self.file_logger.debug('Received logon response {}.'.format(rcv))
        if 35 not in rcv or rcv[35] != b'A':
            self.file_logger.debug('Unexpected logon response.')
            raise Exception('Unexpected logon response : {0}.'.format(rcv))

    def logoff(self):
        """
        Logoff from server.
        """
        self._client.sendlogoff()
        rcv = self._client.receive(timeout=self.cfg.logoff_timeout)
        self.file_logger.debug('Received logoff response {}.'.format(rcv))
        if 35 not in rcv or rcv[35] != b'5':
            self.file_logger.debug(
                'Unexpected logoff response {}'.format(rcv))
            self.logger.error(
                'Fixclient {}: received unexpected logoff response : {}'.format(
                    self.cfg.name, rcv))

    def send(self, msg):
        """
        Send message.

        :param msg: Message to be sent.
        :type msg: ``FixMessage``

        :return: msg
        :rtype: ``FixMessage``
        """
        return self._client.send(msg)[1]

    def send_tsp(self, msg):
        """
        Send message.

        :param msg: Message to be sent.
        :type msg: ``FixMessage``

        :return: Timestamp when msg sent (in microseconds from epoch) and msg.
        :rtype: ``tuple`` of ``long`` and ``FixMessage``
        """
        return self._client.send(msg)

    def receive(self, timeout=None):
        """
        Receive message.

        :param timeout: Timeout in seconds.
        :type timeout: ``int``

        :return: received ``FixMessage`` object
        :rtype: ``FixMessage``
        """
        timeout = timeout if timeout is not None else self.cfg.receive_timeout
        timeout_info = TimeoutExceptionInfo()
        try:
            received = self._client.receive(timeout=timeout)
        except socket.timeout:
            self.logger.error(
                'Timed out waiting for message for {} seconds.'.format(
                    timeout))
            raise TimeoutException(
                'Timed out waiting for message on {0}. {1}'.format(
                    self.cfg.name, timeout_info.msg()))
        self.file_logger.debug('Received msg {}.'.format(received))
        return received

    def flush(self, timeout=0):
        """
        Flush all inbound messages.

        :param timeout: Message receive timeout in seconds. Default: 0
        :type timeout: ``int``
        """
        while True:
            try:
                self.receive(timeout=timeout)
            except TimeoutException:
                break
            except socket.error:
                break

    def _stop_logic(self):
        if self._client:
            try:
                self.logoff()
            except socket.error as err:
                if err.errno != errno.EPIPE:
                    # Not a broken pipe
                    raise
            self._client.close()
            self._client = None
            self.file_logger.debug('Stopped client')

    def stopping(self):
        """Stops the FIX client."""
        super(FixClient, self).stopping()
        self._stop_logic()

    def aborting(self):
        """Abort logic that stops the FIX client."""
        self._stop_logic()
