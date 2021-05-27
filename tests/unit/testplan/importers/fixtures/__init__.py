from dataclasses import dataclass
from pathlib import Path

from testplan.report import TestReport


@dataclass
class ImporterTestFixture:
    input_pah: Path
    expected_report: TestReport
