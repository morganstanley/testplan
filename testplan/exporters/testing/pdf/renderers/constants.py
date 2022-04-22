""" TODO """
from reportlab.lib.pagesizes import A3
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

from testplan.common.exporters.pdf import RowStyle, constants

# Base layout table
COL_WIDTHS = (0.2, 0.375, 0.375, 0.05)

NUM_COLUMNS = len(COL_WIDTHS)

LAST_COLUMN_IDX = NUM_COLUMNS - 1
EMPTY_ROW = ("",) * NUM_COLUMNS

# Font name for normal text
FONT = "Helvetica"

# Font name for bold text
FONT_BOLD = "Helvetica-Bold"

# Font name for Italic text
FONT_ITALIC = "Helvetica-Italic"

# Font name for italic text
FONT_ITALIC = "Helvetica-Oblique"

# Font size for normal text
FONT_SIZE = 11

# Font size for large text
FONT_SIZE_LARGE = 14

# Font size for small text
FONT_SIZE_SMALL = 9

# Font size for smallest text
FONT_SIZE_SMALLEST = 7

# Indent size in pixels
INDENT = 10

# Small indent size in pixels
INDENT_SMALL = 8

# Space between instance reports
INSTANCE_PADDING = 5

# Size of margins on report pages
PAGE_MARGIN = 0.5 * cm

# Size of report pages
PAGE_SIZE = A3
MAX_CELL_HEIGHT = (
    PAGE_SIZE[1] - PAGE_MARGIN * 2 - 30
)  # some extra safeguard margin

# Global style commands for table, can be overridden
TABLE_STYLE = [
    ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
    ("FONT", (0, 0), (-1, -1), FONT, FONT_SIZE),
    ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
]

# Displayed tables constants and style, used for table.log, table.match etc.
PAGE_WIDTH = PAGE_SIZE[0] - PAGE_MARGIN * 2

NUM_DISPLAYED_ROWS = constants.NUM_DISPLAYED_ROWS

CELL_STRING_LENGTH = constants.CELL_STRING_LENGTH

INNER_BORDER = constants.INNER_BORDER

OUTER_BORDER = constants.OUTER_BORDER

DISPLAYED_TABLE_STYLE = [
    RowStyle(
        start_column=0,
        end_column=-1,
        start_row=0,
        end_row=-1,
        font=(FONT, FONT_SIZE_SMALL),
        innergrid=(INNER_BORDER, colors.black),
        box=(OUTER_BORDER, colors.black),
    ),
    RowStyle(
        start_column=0,
        end_column=-1,
        start_row=0,
        end_row=0,
        background=(colors.whitesmoke),
        linebelow=(OUTER_BORDER, colors.black),
    ),
]

# Space between lines in a paragraph
COMPACT_LINE_SPACING = 2

PARAGRAPH_STYLE = ParagraphStyle(
    "default",
    fontSize=FONT_SIZE_SMALL,
    fontName=FONT,
    textColor=colors.black,
    leading=max(FONT_SIZE, FONT_SIZE_SMALL + COMPACT_LINE_SPACING),
    wordWrap="CJK",  # split a long line by length, don't care about words
)

# Space after a testplan heading
TITLE_PADDING = 16

WRAP_LIMITS = {
    FONT_SIZE: 100,
    FONT_SIZE_SMALL: 150,
    FONT_SIZE_SMALLEST: 200,
    FONT_SIZE_LARGE: 80,
}
