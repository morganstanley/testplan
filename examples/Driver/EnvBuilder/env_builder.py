"""
This demonstrates one possible way of implementing of EnvBuilder class.
"""
import functools

from testplan.common.utils.context import context
from testplan.testing.multitest.driver.tcp import TCPClient, TCPServer


class EnvBuilder:
    def __init__(self, env_name: str, drivers: list):
        """
        :param env_name: name of this env builder
        :param drivers: list of drivers to be created
        """
        self.env_name = env_name
        self.drivers = drivers
        self.client_auto_connect = False if len(self.drivers) == 3 else True
        self._client1 = None
        self._client2 = None
        self._server1 = None

    def build_env(self):
        return [getattr(self, driver_name) for driver_name in self.drivers]

    def init_ctx(self):
        return {"env_name": self.env_name}

    def build_deps(self):
        if len(self.drivers) == 2:
            return {self.server1: self.client1}
        elif len(self.drivers) == 3:
            return {self.server1: (self.client1, self.client2)}

    @property
    # @functools.cached_property
    def client1(self):
        if not self._client1:
            self._client1 = TCPClient(
                name="client1",
                host=context("server1", "{{host}}"),
                port=context("server1", "{{port}}"),
                connect_at_start=self.client_auto_connect,
            )
        return self._client1

    @property
    # @functools.cached_property
    def client2(self):
        if not self._client2:
            self._client2 = TCPClient(
                name="client2",
                host=context("server1", "{{host}}"),
                port=context("server1", "{{port}}"),
                connect_at_start=self.client_auto_connect,
            )
        return self._client2

    @property
    # @functools.cached_property
    def server1(self):
        if not self._server1:
            self._server1 = TCPServer(name="server1")
        return self._server1
