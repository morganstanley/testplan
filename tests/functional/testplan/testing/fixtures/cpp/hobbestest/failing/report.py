from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="My HobbesTest",
            category="hobbestest",
            entries=[
                TestGroupReport(
                    name="Hog",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="MultiDestination",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "MultiDestination",
                                    "line_no": None,
                                    "content": "[Hog/MultiDestination]: Failed to connect to log consumer for group "
                                    "'Space' on socket '/var/tmp/hstore.Space.sk' (Unable to connect socket: "
                                    "Connection refused)",
                                    "meta_type": "assertion",
                                    "passed": False,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="KillAndResume",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "KillAndResume",
                                    "line_no": None,
                                    "content": "[Hog/KillAndResume]: Expression false, expected true: c.compileFn<bool()>"
                                    '("f0.seq[0:] == [3,2,1,0]")() (Hog.C:372)',
                                    "meta_type": "assertion",
                                    "passed": False,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="RestartEngine",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "RestartEngine",
                                    "line_no": None,
                                    "content": "18.4997s",
                                    "meta_type": "assertion",
                                    "passed": True,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="Cleanup",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "Cleanup",
                                    "line_no": None,
                                    "content": "140.089ms",
                                    "meta_type": "assertion",
                                    "passed": True,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="Net",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="syncClientAPI",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "syncClientAPI",
                                    "line_no": None,
                                    "content": "4.66587s",
                                    "meta_type": "assertion",
                                    "passed": True,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="asyncClientAPI",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "asyncClientAPI",
                                    "line_no": None,
                                    "content": "1.4305s",
                                    "meta_type": "assertion",
                                    "passed": True,
                                    "type": "RawAssertion",
                                }
                            ],
                        ),
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="Recursives",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="Lists",
                            entries=[
                                {
                                    "category": "DEFAULT",
                                    "description": "Lists",
                                    "line_no": None,
                                    "content": "2.98303s",
                                    "meta_type": "assertion",
                                    "passed": True,
                                    "type": "RawAssertion",
                                }
                            ],
                        )
                    ],
                    tags=None,
                ),
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="ExitCodeCheck",
                            entries=[
                                {"type": "RawAssertion", "passed": True},
                                {
                                    "type": "Attachment",
                                    "description": "Process stdout",
                                },
                                {
                                    "type": "Attachment",
                                    "description": "Process stderr",
                                },
                            ],
                        ),
                    ],
                ),
            ],
            tags=None,
        )
    ],
)
