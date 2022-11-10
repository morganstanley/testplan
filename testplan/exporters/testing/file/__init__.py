from typing import Callable

from testplan.common.exporters import ExporterConfig
from testplan.exporters.testing.base import Exporter
from testplan.report.testing.base import TestReport


class FileExporter(Exporter):
    """
    File exporter acting as a backdoor for custom output tasks
    """

    CONFIG = ExporterConfig

    def __init__(
        self,
        callback: Callable[[TestReport], None],
        name: str = "Custom File Exporter",
        **options
    ):
        self.callback = callback  # currently we do not log callback
        super(FileExporter, self).__init__(name=name, **options)

    def export(self, source: TestReport):
        if len(source):
            self.callback(source)
