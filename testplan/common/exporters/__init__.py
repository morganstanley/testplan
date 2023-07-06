"""TODO."""
import traceback

from dataclasses import dataclass, field
from typing import Dict, List, Optional

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


def _verify_export_context(
    exporter: BaseExporter, export_context: Optional[ExportContext]
) -> ExportContext:
    """
    Verifies whether export context is present and creates an empty one if not.

    :param: exporter: actual exporter being run
    :param: export_context: information about other exporters
    :return: ExportContext object containing information about exporters
    """

    # TODO: Remove this function after the grace period
    if export_context is None:
        exporter.logger.warning(
            (
                "Exporter '%s' does not have keyword_argument 'export_context'! "
                "This will be prohibited in the future, please modify your custom exporter!"
            ),
            exporter,
        )
        return ExportContext()
    else:
        return export_context


def _run_exporter(
    exporter: BaseExporter,
    source: TestReport,
    export_context: ExportContext,
) -> None:
    """
    Wraps an exporter run and handles exceptions.

    :param exporter: exporter to run
    :param source: Testplan report to export
    :param export_context: ExportContext object for storing information about other exporters
    """

    traceback_string = None
    exp_result = None
    try:
        exp_result = exporter.export(
            source=source,
            export_context=export_context,
        )
    except TypeError:
        # TODO: Remove this except section after the grace period
        exporter.logger.warning(
            (
                "Exporter '%s' does not have keyword_argument 'export_context'! "
                "This will be prohibited in the future, please modify your custom exporter!"
            ),
            exporter,
        )
        exp_result = exporter.export(
            source=source,
        )
    except Exception:
        traceback_string = traceback.format_exc()
    finally:
        if isinstance(exp_result, ExporterResult):
            exp_result.traceback = traceback_string
        else:
            if not traceback_string:
                # TODO: Move this part to the Exception section and remove the else block after the grace period
                # We probably did not fail during the export
                exporter.logger.warning(
                    (
                        "Exporter '%s' returns with not an ExporterResult object! "
                        "This will be prohibited in the future, please modify your custom exporter!"
                    ),
                    exporter,
                )
            exp_result = ExporterResult(
                exporter=exporter,
                traceback=traceback_string,
                result={"unknown": exp_result},
            )
        if not exp_result.success:
            exporter.logger.error(exp_result.traceback)
        export_context.results.append(exp_result)
