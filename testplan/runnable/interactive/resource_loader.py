"""Import classes on runtime."""


class ResourceLoader:
    """Load logic."""

    def load(self, name, kwargs):
        """Load the registered object for the given name."""
        target_class = getattr(self, "_load_{}".format(name))()
        return target_class(**kwargs)

    def _load_TCPServer(self):
        from testplan.testing.multitest.driver.tcp import TCPServer

        return TCPServer

    def _load_TCPClient(self):
        from testplan.testing.multitest.driver.tcp import TCPClient

        return TCPClient
