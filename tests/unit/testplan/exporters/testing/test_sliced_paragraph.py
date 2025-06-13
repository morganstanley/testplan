from html import escape

from reportlab.platypus import Paragraph
from testplan.exporters.testing.pdf.renderers import constants
from testplan.exporters.testing.pdf.renderers.base import SlicedParagraph


def test_sliced_para():
    msg = (
        "This is a super looooooooooong message with indents, extra spaces\n"
        "    and <Test>special</Test> characters,\n"
        "    and    it    will    be    written    as-is    in    pdf.\n"
    )

    para = Paragraph(
        text=escape(msg, quote=False)
        .replace("\n", "<br/>")
        .replace(" ", "&nbsp;"),
        style=constants.PARAGRAPH_STYLE,
    )
    width, height = para.wrap(constants.PAGE_WIDTH, constants.MAX_CELL_HEIGHT)

    assert (
        sum(
            1
            for _ in SlicedParagraph(
                parts=[(msg, "{}")] * 3,
                width=width,
                height=height,
            )
        )
        == 3
    )
