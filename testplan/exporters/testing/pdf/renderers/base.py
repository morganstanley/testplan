"""Base classes for rendering """
import collections
import functools

from testplan.common.exporters.pdf import RowData

from . import constants


RowData = functools.partial(RowData, num_columns=constants.NUM_COLUMNS)


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


class BaseRowRenderer(object):
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


class MetadataMixin(object):
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
        return collections.OrderedDict(
            [
                (label, source.meta[key])
                for key, label in self.get_metadata_labels()
                if source.meta.get(key)
            ]
        )
