"""TODO."""
from dataclasses import dataclass, field
from typing import Dict, List

from testplan.common.config import Config, Configurable
from testplan.report import TestReport


@dataclass
class ExporterResult:
    exporter: "BaseExporter"
    result: Dict = None
    traceback: str = None

    @property
    def success(self) -> bool:
        return not self.traceback


@dataclass
class ExportContext:
    """Dataclass for storing information about exporters."""

    results: List[ExporterResult] = field(default_factory=list)


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

    def __str__(self):
        return f"{self.__class__.__name__}[{self.name}]"

    @property
    def name(self):
        return self.cfg.name

    @property
    def cfg(self):
        """Exporter configuration."""
        return self._cfg

    def export(
        self,
        source: TestReport,
        export_context: ExportContext,
    ) -> ExporterResult:
        """
        Pseudo export function.

        :param: source: Testplan report export
        :param: export_context: information about other exporters
        :return: ExporterResult object containing information about the actual exporter object and its possible output
        """
        raise NotImplementedError("Exporter must define export().")
