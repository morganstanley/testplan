"""The xUnit importers must read reports as the documents declare themselves.

These files carry an XML prolog announcing UTF-8. Opening them in text mode
handed the bytes to ``locale.getpreferredencoding()`` before lxml could read
that prolog, which crashed on a DBCS host and, worse, produced silent mojibake
on cp1252 - the default ANSI codepage on en-US Windows, including the
``windows-latest`` CI leg.
"""

import os
import subprocess
import sys
import textwrap

import pytest


# A euro sign is enough: it is representable in cp1252 (as a different byte
# sequence, hence mojibake rather than a crash) and unrepresentable in cp950,
# so the same fixture exercises both failure modes depending on the host.
NON_ASCII_TESTCASE = "charges_€100_fee"

GTEST_REPORT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="1" failures="0" errors="0" name="AllTests">
  <testsuite name="Fees" tests="1" failures="0" errors="0">
    <testcase name="{name}" status="run" classname="Fees"/>
  </testsuite>
</testsuites>
"""

JUNIT_REPORT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="Fees" tests="1" failures="0" errors="0" skipped="0">
    <testcase name="{name}" classname="Fees" time="0.01"/>
  </testsuite>
</testsuites>
"""

# CppUnit names are "Suite::case"; the XSLT splits on "::", so the fixture
# has to carry the separator or the transformed name comes out empty.
CPPUNIT_REPORT = """<?xml version="1.0" encoding="UTF-8"?>
<TestRun>
  <SuccessfulTests>
    <Test id="1">
      <Name>Fees::{name}</Name>
    </Test>
  </SuccessfulTests>
  <Statistics>
    <Tests>1</Tests>
    <FailuresTotal>0</FailuresTotal>
    <Errors>0</Errors>
    <Failures>0</Failures>
  </Statistics>
</TestRun>
"""

# The importers run in a child interpreter with a legacy locale forced on.
# Without this the test passes on a UTF-8 host whether or not the fix is
# present, which is exactly how this survived in CI.
LEGACY_LOCALE_ENV = {
    "PYTHONUTF8": "0",
    "PYTHONCOERCECLOCALE": "0",
    "LC_ALL": "C",
    "LANG": "C",
}

PARSE_SCRIPT = textwrap.dedent(
    """
    import sys
    from lxml import etree

    module_name, path = sys.argv[1], sys.argv[2]
    if module_name == "gtest":
        from testplan.importers.gtest import GTestResultImporter as Importer
    elif module_name == "junit":
        from testplan.importers.junit import JUnitResultImporter as Importer
    else:
        from testplan.importers.cppunit import CPPUnitResultImporter as Importer

    root = Importer(path, name="n", description="d")._read_data(path)
    sys.stdout.buffer.write(etree.tostring(root, encoding="utf-8"))
    """
)


@pytest.mark.parametrize(
    "importer_name, template",
    [
        ("gtest", GTEST_REPORT),
        ("junit", JUNIT_REPORT),
        ("cppunit", CPPUNIT_REPORT),
    ],
)
def test_importer_reads_utf8_report_under_legacy_locale(
    importer_name, template, tmp_path
):
    """A UTF-8 report imports identically regardless of the host locale."""
    report = tmp_path / f"{importer_name}.xml"
    report.write_bytes(
        template.format(name=NON_ASCII_TESTCASE).encode("utf-8")
    )

    script = tmp_path / "parse.py"
    script.write_text(PARSE_SCRIPT, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script), importer_name, str(report)],
        capture_output=True,
        env={**os.environ, **LEGACY_LOCALE_ENV},
    )

    # Catches the crash: on a DBCS or ASCII locale the read raises and the
    # import dies before producing anything.
    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", "replace"
    )

    # Catches the silent corruption. Assert on the bytes the child produced,
    # decoded as UTF-8 - comparing strings read back through the same broken
    # default would round-trip the mojibake and pass either way.
    assert NON_ASCII_TESTCASE in completed.stdout.decode("utf-8")


def test_ascii_report_is_unaffected(tmp_path):
    """The ASCII path the existing fixtures cover behaves identically.

    Present as a control: it passes with and without the fix, so a failure
    here means the harness broke rather than the encoding handling.
    """
    report = tmp_path / "gtest.xml"
    report.write_bytes(GTEST_REPORT.format(name="charges_fee").encode("utf-8"))

    script = tmp_path / "parse.py"
    script.write_text(PARSE_SCRIPT, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script), "gtest", str(report)],
        capture_output=True,
        env={**os.environ, **LEGACY_LOCALE_ENV},
    )

    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", "replace"
    )
    assert "charges_fee" in completed.stdout.decode("utf-8")
