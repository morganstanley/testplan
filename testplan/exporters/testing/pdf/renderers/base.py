"""
Base classes for rendering.
"""
import collections
import functools
from html import escape

from reportlab.platypus import Paragraph

from testplan.common.exporters.pdf import RowData
from . import constants

RowData = functools.partial(RowData, num_columns=constants.NUM_COLUMNS)


class SlicedParagraph:
    """
    Iterator which returns slices of ReportLab Paragraph to make sure each does
    not exceed max height (which will trigger ReportLab LayoutError).

    :param parts: list of (text, formatter) tuple
    :type parts: [(``str``, ``str``), ...]
    :param width: width allowed to layout each paragraph
    :type width: ``int``
    :param height: height allowed to layout each paragraph
    :type height: ``int``
    :param style: style object for paragraph
    :type style: ReportLab ParagraphStyle

    """

    def __init__(
        self,
        parts,
        width,
        height=constants.MAX_CELL_HEIGHT,
        style=constants.PARAGRAPH_STYLE,
        **kwargs
    ):
        self.width = width
        self.height = height

        text_parts = []
        if not isinstance(parts, list):
            parts = [parts]

        for part, formatter in parts:
            # reserve indentation - report lab does not wrap at '\n' and removes space
            part = (
                escape(part, quote=False)
                .replace("\n", "<br/>")
                .replace(" ", "&nbsp;")
            )
            text_parts.append(formatter.format(part))

        self.para = Paragraph(text="".join(text_parts), style=style, **kwargs)

    def __next__(self):
        if self.para:
            paras = self.para.split(self.width, self.height)
            # paras == [] for empty line
            para = paras[0] if paras else ""
            self.para = paras[1] if len(paras) == 2 else None
            return para
        else:
            raise StopIteration

    def __iter__(self):
        return self


def format_duration(seconds):
    """
    Format a duration into a human-readable string.
    """
    mins, secs = divmod(seconds, 60)
    fmt = "{:.0f}"
    if mins:
        return "{} minutes {} seconds".format(fmt, fmt).format(mins, secs)
    else:
        return "{} seconds".format(fmt).format(secs)


class BaseRowRenderer:
    """Base class for row renderers."""

    always_display = False

    def __init__(self, style):
        self.style = style

    def get_row_data(self, source, depth, row_idx):
        """
        Return `RowData` to be rendered on the pdf.

        :param source: Source object for the renderer.
        :type source: ``report.base.Report`` or ``dict`` (for assertion data).
        :param depth: Depth of the source object on report tree.
                      Used for indentation.
        :type depth: ``int``
        :param row_idx: Index of the current table row to be rendered.
        :type row_idx: ``int``
        :return: ``RowData`` object.
        :rtype: ``exporters.utils.pdf.RowData``
        """
        raise NotImplementedError

    def get_style(self, source):
        return self.style.passing

    def should_display(self, source):
        """Use class attribute by default."""
        return (
            self.always_display
            or self.get_style(source).display_assertion_detail
        )


class MetadataMixin:
    """
    Utility mixin that has logic for getting
    metadata context for row renderers.

    Basically we'd like to selectively render the
    information stored in `meta` dictionary, with readable labels.
    """

    metadata_labels = ()

    def get_metadata_labels(self):
        """Wrapper around class attribute, so we can support inheritance."""
        return self.metadata_labels

    def get_metadata_context(self, source):
        """
        Return metadata context to be rendered
        on the PDF with readable labels.
        """
        metadata = dict(source.information)
        return collections.OrderedDict(
            [
                (label, metadata[key][:5000])
                for key, label in self.get_metadata_labels()
                if key in metadata
            ]
        )
