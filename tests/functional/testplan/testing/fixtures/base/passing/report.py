import re
from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    TestCaseReport,
    TestGroupReport,
    TestReport,
)

testcase_report = TestCaseReport(
    name="ExitCodeCheck",
    category=ReportCategories.SYNTHESIZED,
    entries=[
        {
            "type": "RawAssertion",
            "description": "Process exit code check",
            "passed": True,
        },
        {"type": "Attachment", "description": "Process stdout"},
        {"type": "Attachment", "description": "Process stderr"},
    ],
)

testcase_report.runtime_status = RuntimeStatus.FINISHED

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="dummytest",
            entries=[
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[testcase_report],
                ),
            ],
        ),
    ],
)


expected_report_with_driver = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="dummytest",
            entries=[
                TestGroupReport(
                    name="Environment Start",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Starting",
                            uid="Starting",
                            description="",
                            entries=[],
                        )
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[testcase_report],
                ),
                TestGroupReport(
                    name="Environment Stop",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Stopping",
                            uid="Stopping",
                            description="",
                            entries=[],
                        )
                    ],
                    tags=None,
                ),
            ],
        ),
    ],
)

expected_report_with_driver_and_driver_info_flag = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="multitest",
            entries=[
                TestGroupReport(
                    name="Environment Start",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Starting",
                            uid="Starting",
                            description="",
                            entries=[
                                {
                                    "type": "TableLog",
                                    "indices": [0],
                                    "display_index": False,
                                    "columns": [
                                        "Driver Class",
                                        "Driver Name",
                                        "Start Time (UTC)",
                                        "Stop Time (UTC)",
                                        "Duration(seconds)",
                                    ],
                                    "category": "DEFAULT",
                                    "table": [
                                        [
                                            "Driver",
                                            "driver",
                                            re.compile(
                                                r"\d{2}:\d{2}:\d{2}.\d{6}"
                                            ),
                                            re.compile(
                                                r"\d{2}:\d{2}:\d{2}.\d{6}"
                                            ),
                                            lambda x: isinstance(x, float),
                                        ]
                                    ],
                                    "description": "Driver Setup Info",
                                    "meta_type": "entry",
                                },
                                {
                                    "style": None,
                                    "type": "Plotly",
                                    "filesize": lambda x: isinstance(x, int),
                                    "dst_path": re.compile(r".*\.json"),
                                    "category": "DEFAULT",
                                    "source_path": re.compile(r".*\.json"),
                                    "orig_filename": re.compile(r".*\.json"),
                                    "description": "Driver Setup Timeline",
                                    "meta_type": "entry",
                                },
                            ],
                        )
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="Environment Stop",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Stopping",
                            uid="Stopping",
                            description="",
                            entries=[
                                {
                                    "type": "TableLog",
                                    "indices": [0],
                                    "display_index": False,
                                    "columns": [
                                        "Driver Class",
                                        "Driver Name",
                                        "Start Time (UTC)",
                                        "Stop Time (UTC)",
                                        "Duration(seconds)",
                                    ],
                                    "category": "DEFAULT",
                                    "table": [
                                        [
                                            "Driver",
                                            "driver",
                                            re.compile(
                                                r"\d{2}:\d{2}:\d{2}.\d{6}"
                                            ),
                                            re.compile(
                                                r"\d{2}:\d{2}:\d{2}.\d{6}"
                                            ),
                                            lambda x: isinstance(x, float),
                                        ]
                                    ],
                                    "description": "Driver Teardown Info",
                                    "meta_type": "entry",
                                },
                                {
                                    "style": None,
                                    "type": "Plotly",
                                    "filesize": lambda x: isinstance(x, int),
                                    "dst_path": re.compile(r".*\.json"),
                                    "category": "DEFAULT",
                                    "source_path": re.compile(r".*\.json"),
                                    "orig_filename": re.compile(r".*\.json"),
                                    "description": "Driver Teardown Timeline",
                                    "meta_type": "entry",
                                },
                            ],
                        )
                    ],
                    tags=None,
                ),
            ],
        ),
    ],
)

expected_report_with_driver_and_driver_connection_flag = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="multitest",
            entries=[
                TestGroupReport(
                    name="Environment Start",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Starting",
                            uid="Starting",
                            description="",
                            entries=[
                                {
                                    "type": "FlowLog",
                                    "category": "DEFAULT",
                                    "description": "Driver Connections",
                                    "nodes": [
                                        "TCPServer[server]",
                                        "FXConverter[converter]",
                                        "TCPClient[client]",
                                    ],
                                    "edges": [
                                        {
                                            "id": re.compile(
                                                r"tcp:\/\/:\d{1,5}-TCPServer\[server\]-FXConverter\[converter\]"
                                            ),
                                            "source": "TCPServer[server]",
                                            "target": "FXConverter[converter]",
                                            "startLabel": re.compile(
                                                r"\d{1,5}"
                                            ),
                                            "label": re.compile(
                                                r"tcp:\/\/:\d{1,5}"
                                            ),
                                            "endLabel": re.compile(r"\d{1,5}"),
                                        },
                                        {
                                            "id": re.compile(
                                                r"tcp:\/\/:\d{1,5}-FXConverter\[converter\]-TCPClient\[client\]"
                                            ),
                                            "source": "FXConverter[converter]",
                                            "target": "TCPClient[client]",
                                            "startLabel": re.compile(
                                                r"\d{1,5}"
                                            ),
                                            "label": re.compile(
                                                r"tcp:\/\/:\d{1,5}"
                                            ),
                                            "endLabel": re.compile(r"\d{1,5}"),
                                        }
                                    ],
                                },
                            ],
                        ),
                        TestCaseReport(
                            name="After Start",
                            uid="After Start",
                            description="Called right after MultiTest starts.",
                            entries=[],
                        )
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="Environment Stop",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Before Stop",
                            uid="Before Stop",
                            description="Called right before MultiTest stops.",
                            entries=[],
                        ),
                        TestCaseReport(
                            name="Stopping",
                            uid="Stopping",
                            description="",
                            entries=[],
                        )
                    ],
                    tags=None,
                ),
            ],
        ),
    ],
)
