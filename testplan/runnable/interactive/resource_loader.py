"""Import classes on runtime."""


class ResourceLoader(object):
    """Load logic."""

    def load(self, name):
        """Load the registered object for the given name."""
        return getattr(self, '_load_{}'.format(name))()

    def _load_TCPServer(self):
        from testplan.testing.multitest.driver.tcp import TCPServer
        return TCPServer

    def _load_TCPClient(self):
        from testplan.testing.multitest.driver.tcp import TCPClient
        return TCPClient