import tempfile
from itertools import count
from pathlib import Path

import pytest
from click.testing import CliRunner

from testplan.cli.tpsreport import cli

# tpsreport command should already be available after installation
# TODO: to be refactored with jq (apply jq op on gened data before diff)

# NOTE: useful when normalise test data
# $ jq 'walk( if type == "object" and has("uid") then .uid = "" | .hash = "" else . end )' data > data_


DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "from_cmd, input_file, to_cmd",
    [
        ("fromjson", "old.data", ["tojson"]),
        ("fromjson", "curr.data", ["tojson"]),
        ("fromjson", "old2.data", ["topdf", "--pdf-style", "detailed"]),
        ("fromjson", "curr2.data", ["topdf", "--pdf-style", "detailed"]),
    ],
    ids=count(0),
)
def test_convert(from_cmd, input_file, to_cmd):
    input_file = str(DATA_DIR / input_file)
    runner = CliRunner()
    try:
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        result = runner.invoke(
            cli, ["convert", from_cmd, input_file] + to_cmd + [f.name]
        )
        assert result.exit_code == 0
    finally:
        Path(f.name).unlink()
