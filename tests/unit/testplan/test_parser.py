from testplan import TestplanMock
from testplan.testing.listing import SimpleJsonLister, NameLister


def test_info_output_parsing(runpath):
    # we let the mockplan to create the parser as the plan:
    # populate an insane number of defaults, which the parser
    # rely on.
    mockplan = TestplanMock("plan", runpath=runpath, parse_cmdline=False)
    parser = mockplan.parser.generate_parser()
    args = parser.parse_args(["--info", "json"])

    assert isinstance(args.test_lister, SimpleJsonLister)
    assert args.test_lister_output is None

    args = parser.parse_args(["--info", "json:/tmp/a.json"])

    assert isinstance(args.test_lister, SimpleJsonLister)
    assert args.test_lister_output == "/tmp/a.json"
