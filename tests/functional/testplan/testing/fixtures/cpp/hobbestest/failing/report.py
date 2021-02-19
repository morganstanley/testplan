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
                                    u"category": u"DEFAULT",
                                    u"description": u"MultiDestination",
                                    u"line_no": None,
                                    u"content": u"[Hog/MultiDestination]: Failed to connect to log consumer for group "
                                    u"'Space' on socket '/var/tmp/hstore.Space.sk' (Unable to connect socket: "
                                    u"Connection refused)",
                                    u"meta_type": u"assertion",
                                    u"passed": False,
                                    u"type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="KillAndResume",
                            entries=[
                                {
                                    u"category": u"DEFAULT",
                                    u"description": u"KillAndResume",
                                    u"line_no": None,
                                    u"content": u"[Hog/KillAndResume]: Expression false, expected true: c.compileFn<bool()>"
                                    u'("f0.seq[0:] == [3,2,1,0]")() (Hog.C:372)',
                                    u"meta_type": u"assertion",
                                    u"passed": False,
                                    u"type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="RestartEngine",
                            entries=[
                                {
                                    u"category": u"DEFAULT",
                                    u"description": u"RestartEngine",
                                    u"line_no": None,
                                    u"content": u"18.4997s",
                                    u"meta_type": u"assertion",
                                    u"passed": True,
                                    u"type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="Cleanup",
                            entries=[
                                {
                                    u"category": u"DEFAULT",
                                    u"description": u"Cleanup",
                                    u"line_no": None,
                                    u"content": u"140.089ms",
                                    u"meta_type": u"assertion",
                                    u"passed": True,
                                    u"type": "RawAssertion",
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
                                    u"category": u"DEFAULT",
                                    u"description": u"syncClientAPI",
                                    u"line_no": None,
                                    u"content": u"4.66587s",
                                    u"meta_type": u"assertion",
                                    u"passed": True,
                                    u"type": "RawAssertion",
                                }
                            ],
                        ),
                        TestCaseReport(
                            name="asyncClientAPI",
                            entries=[
                                {
                                    u"category": u"DEFAULT",
                                    u"description": u"asyncClientAPI",
                                    u"line_no": None,
                                    u"content": u"1.4305s",
                                    u"meta_type": u"assertion",
                                    u"passed": True,
                                    u"type": "RawAssertion",
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
                                    u"category": u"DEFAULT",
                                    u"description": u"Lists",
                                    u"line_no": None,
                                    u"content": u"2.98303s",
                                    u"meta_type": u"assertion",
                                    u"passed": True,
                                    u"type": "RawAssertion",
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
                                    "type": "Log",
                                    "description": "Process stdout",
                                },
                                {
                                    "type": "Log",
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
