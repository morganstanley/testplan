"""
This script shows how a JSON report can be loaded back
into the memory for further processing.
"""
import argparse
import json

from testplan.report import TestReport
from testplan.exporters.testing import PDFExporter

from testplan.report.testing.styles import Style, StyleEnum


def main(source, target):

    with open(source) as source_file:
        data = json.loads(source_file.read())
        if data.get("split"):
            raise RuntimeError("Cannot process JSON report that was split")

        report_obj = TestReport.deserialize(data)
        print("Loaded report: {}".format(report_obj.name))

        # We can initialize an exporter object directly, without relying on
        # Testplan internals to trigger the export operation.
        exporter = PDFExporter(
            pdf_path=target,
            pdf_style=Style(
                passing=StyleEnum.ASSERTION_DETAIL,
                failing=StyleEnum.ASSERTION_DETAIL,
            ),
        )

        exporter.export(report_obj)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="report.json", type=str)
    parser.add_argument("--target", default="report.pdf", type=str)

    args = parser.parse_args()

    main(source=args.source, target=args.target)
