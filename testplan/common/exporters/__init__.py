"""TODO."""
import traceback
from typing import Optional

from testplan.common.config import Config, Configurable
from testplan.report import TestReport


class ExporterResult:
    def __init__(self, exporter, type):
        self.exporter = exporter
        self.type = type
        self.traceback = None

    @property
    def success(self):
        return not self.traceback

    @classmethod
    def run_exporter(cls, exporter, source, type):
        result = ExporterResult(exporter=exporter, type=type)

        try:
            exporter.export(source)
        except Exception:
            result.traceback = traceback.format_exc()
        return result


class ExporterConfig(Config):
    """
    Configuration object for
    :py:class:`BaseExporter <testplan.common.exporters.BaseExporter>` object.
    """

    @classmethod
    def get_options(cls):
        return {"name": str}


class BaseExporter(Configurable):
    """Base exporter class."""

    CONFIG = ExporterConfig

    def __init__(self, name=None, **options):
        if name is None:
            name = self.__class__.__name__
        self._cfg = self.CONFIG(name=name, **options)
        super().__init__()

    @property
    def name(self):
        return self.cfg.name

    @property
    def cfg(self):
        """Exporter configuration."""
        return self._cfg

    def export(self, source: TestReport) -> Optional[str]:
        raise NotImplementedError("Exporter must define export().")
