"""TODO."""
import traceback

from testplan.common.config import Config, Configurable


class ExporterResult(object):

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
        return {}


class BaseExporter(Configurable):
    """Base exporter class."""

    CONFIG = ExporterConfig

    def __init__(self, **options):
        self._cfg = self.CONFIG(**options)
        super(BaseExporter, self).__init__()

    @property
    def cfg(self):
        """Exporter configuration."""
        return self._cfg

    def export(self, report):
        raise NotImplementedError('Exporter must define export().')
