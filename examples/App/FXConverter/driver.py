"""Driver for converter.py application binary."""

import re

from testplan.testing.multitest.driver.app import App


class FXConverter(App):
    """
    Inherits the generic ``testplan.testing.multitest.driver.app.App`` driver
    and expose host/port values read from log extracts.
    """

    def __init__(self, **options):
        super(FXConverter, self).__init__(**options)
        self.host = None
        self.port = None

    def started_check(self, timeout=None):
        """
        Checks that binary started and input regex conditions matching, while
        also storing host/port information to be made available in its context
        so that client driver can connect to it.
        """
        super(FXConverter, self).started_check(timeout=timeout)
        self.host, self.port = re.split(":", self.extracts["listen_address"])
