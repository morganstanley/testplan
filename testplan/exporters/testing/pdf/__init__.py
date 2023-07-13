"""
PDF Export logic for test reports via ReportLab.
"""

import os
import pathlib
import time
import traceback
import uuid
import warnings
from typing import Dict, Optional
from urllib.request import pathname2url

from schema import Or

from testplan.report import TestReport

try:
    from reportlab.platypus import SimpleDocTemplate
except Exception as exc:
    warnings.warn("reportlab must be supported: {}".format(exc))

try:
    from testplan.common.exporters.pdf import create_base_tables
except Exception as exc:
    warnings.warn("reportlab must be supported: {}".format(exc))


from testplan.common.config import ConfigOption
from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    verify_export_context,
)
from testplan.common.report import Report
from testplan.common.utils.strings import slugify
from testplan.report.testing.styles import Style
from testplan.testing import tagging
from ..base import Exporter
from ..tagfiltered import TagFilteredExporter, TagFilteredExporterConfig

try:
    from . import renderers
    from .renderers import (
        report_registry,
        serialized_entry_registry,
        constants as const,
    )

    stored_exc = None
except Exception as exc:
    warnings.warn("reportlab must be supported: {}".format(exc))
    traceback.print_exc()
    report_registry = None
    serialized_entry_registry = None
    const = None
    stored_exc = exc


MAX_FILENAME_LENGTH = 100


def generate_path_for_tags(config, tag_dict, filter_type):
    """
    Generate the PDF filename using the given filter and tag context.
    Will trim the filename and append a uuid suffix if it ends up
    being longer than `MAX_FILENAME_LENGTH`.

    TOOD: support custom filename generation & move logic to the exporter.

    >>> generate_pdf_path(
    ...   filter_type='all',
    ...   tag_arg_dict={
    ...     'simple': {'foo', 'bar'},
    ...     'hello': {'world', 'mars'}
    ...   }
    ... )

    <directory>/report-tags-all-foo__bar__hello-world-mars.pdf
    """

    def add_count_suffix(directory, path, count=0):
        """Add a number suffix to file name if files with same names exist."""
        target_path = "{}_{}".format(path, count) if count else path
        full_path = os.path.join(config.report_dir, target_path + ".pdf")
        if os.path.exists(full_path):
            return add_count_suffix(directory, path, count + 1)
        return full_path

    tag_label = (
        tagging.tag_label(tag_dict)
        .replace(" ", "__")
        .replace("=", "-")
        .replace(",", "-")
    )
    path_template = "report-tags-{filter_type}-{label}"
    path_kwargs = dict(filter_type=filter_type, label=slugify(tag_label))

    if config.timestamp:
        path_template += "-{timestamp}"
        path_kwargs["timestamp"] = config.timestamp

    path = path_template.format(**path_kwargs)
    if len(path) >= MAX_FILENAME_LENGTH:
        path = "{}-{}".format(path[:MAX_FILENAME_LENGTH], uuid.uuid4())

    return add_count_suffix(config.report_dir, path)


class BasePDFExporterConfig(ExporterConfig):
    """Config for PDF exporter"""

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("timestamp", default=None): Or(str, None),
            ConfigOption("pdf_style"): Style,
        }


class PDFExporterConfig(BasePDFExporterConfig):
    """
    Configuration object for
    :py:class:`PDFExporter <testplan.exporters.testing.pdf.PDFExporter>`
    object.
    """

    @classmethod
    def get_options(cls):
        return {ConfigOption("pdf_path"): str}


class TagFilteredPDFExporterConfig(
    TagFilteredExporterConfig, BasePDFExporterConfig
):
    """
    Configuration object for
    :py:class:`TagFilteredPDFExporter <testplan.exporters.testing.pdf.TagFilteredPDFExporter>`  # pylint: disable=line-too-long
    object.
    """

    @classmethod
    def get_options(cls):
        return {ConfigOption("report_dir"): str}


class PDFExporter(Exporter):
    """
    PDF Exporter.

    :param pdf_path: File path for saving PDF report.
    :type pdf_path: ``str``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = PDFExporterConfig

    def __init__(self, name="PDF exporter", **options):
        super(PDFExporter, self).__init__(name=name, **options)

    def create_pdf(self, source):
        """Entry point for PDF generation."""
        if stored_exc is not None:
            # We cannot generate a PDF if there was an exception importing the
            # dependencies, so raise and abort here.
            #
            # Need to explicitly disable the raising-bad-type check here since
            # pylint isn't smart enough to know that we explicitly checked that
            # the stored_exc is not None above.
            raise stored_exc  # pylint: disable=raising-bad-type

        # Depth values will be used for indentation on PDF, however
        # we want first level children to have depth = 0 (otherwise we'll have to
        # do `depth + 1` everywhere in the renderers.
        # The renderer for root will discard the negative depth.
        data = [(depth - 1, rep) for depth, rep in source.flatten(depths=True)]

        reportlab_data = []
        reportlab_styles = []
        row_idx = 0

        for depth, obj in data:

            registry = (
                report_registry
                if isinstance(obj, Report)
                else serialized_entry_registry
            )

            renderer = registry[obj](style=self.cfg.pdf_style)
            if renderer.should_display(source=obj):
                row_data = renderer.get_row_data(
                    source=obj, depth=depth, row_idx=row_idx
                )
                row_idx = row_data.end

                reportlab_data.extend(row_data.content)
                reportlab_styles.extend(row_data.style)

        pdf_path = pathlib.Path(self.cfg.pdf_path).resolve()
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if self.cfg.interactive_port is None:
                override = True
            else:
                override = False
        except AttributeError:
            override = True
        if not override and pdf_path.exists():
            pdf_path = pdf_path.with_name(
                f"{pdf_path.stem}_{int(time.time())}{pdf_path.suffix}"
            )
            self.logger.error("File %s exists!", self.cfg.pdf_path)

        template = SimpleDocTemplate(
            filename=str(pdf_path),
            pagesize=const.PAGE_SIZE,
            topMargin=const.PAGE_MARGIN,
            bottomMargin=const.PAGE_MARGIN,
            leftMargin=const.PAGE_MARGIN,
            rightMargin=const.PAGE_MARGIN,
            title="Testplan report - {}".format(source.name),
        )

        tables = create_base_tables(
            data=reportlab_data,
            style=const.TABLE_STYLE + reportlab_styles,
            col_widths=[width * template.width for width in const.COL_WIDTHS],
        )

        template.build(tables)
        return str(pdf_path)

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> Optional[Dict]:
        """
        Exports report to PDF in the given directory.

        :param: source: Testplan report to export
        :param: export_context: information about other exporters
        :return: dictionary containing the possible output
        """

        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        result = None
        if len(source):
            pdf_path = self.create_pdf(source)
            self.logger.user_info("PDF generated at %s", pdf_path)

            self.url = f"file:{pathname2url(pdf_path)}"
            result = {"pdf": pdf_path}
        else:
            self.logger.user_info(
                "Skipping PDF creation for empty report: %s", source.name
            )
        return result


class TagFilteredPDFExporter(TagFilteredExporter):
    """
    Tag filtered PDF Exporter.

    :param report_dir: Directory for saving PDF reports.
    :type report_dir: ``str``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.TagFilteredExporter` options.
    """

    CONFIG = TagFilteredPDFExporterConfig
    exporter_class = PDFExporter

    def get_params(self, tag_dict, filter_type):
        return {
            "pdf_path": generate_path_for_tags(self.cfg, tag_dict, filter_type)
        }
