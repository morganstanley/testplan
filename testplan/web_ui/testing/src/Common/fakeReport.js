/**
 * Sample Testplan reports to be used in development & testing.
 */
const TESTPLAN_REPORT = {
  "name": "Sample Testplan",
  "status": "failed",
  "uid": "520a92e4-325e-4077-93e6-55d7091a3f83",
  "tags_index": {},
  "information": [
    [
        "user",
        "unknown"
    ],
    [
        "command_line_string",
        "/home/unknown/path_to_testplan_script/testplan.py"
    ],
  ],
  "status_override": null,
  "meta": {},
  "timer": {
    "run": {
      "start": "2018-10-15T14:30:10.998071+00:00",
      "end": "2018-10-15T14:30:11.296158+00:00"
    }
  },
  "entries": [
    {
      "name": "Primary",
      "status": "failed",
      "category": "multitest",
      "description": null,
      "status_override": null,
      "uid": "21739167-b30f-4c13-a315-ef6ae52fd1f7",
      "type": "TestGroupReport",
      "logs": [],
      "tags": {
        "simple": ["server"]
      },
      "timer": {
        "run": {
          "start": "2018-10-15T14:30:11.009705+00:00",
          "end": "2018-10-15T14:30:11.159661+00:00"
        }
      },
      "entries": [
        {
          "status": "failed",
          "category": "testsuite",
          "name": "AlphaSuite",
          "status_override": null,
          "description": "This is a failed testsuite",
          "uid": "cb144b10-bdb0-44d3-9170-d8016dd19ee7",
          "type": "TestGroupReport",
          "logs": [],
          "tags": {
            "simple": ["server"]
          },
          "timer": {
            "run": {
              "start": "2018-10-15T14:30:11.009872+00:00",
              "end": "2018-10-15T14:30:11.158224+00:00"
            }
          },
          "entries": [
            {
              "name": "test_equality_passing",
              "category": "testcase",
              "status": "passed",
              "status_override": null,
              "description": "A testcase example",
              "uid": "736706ef-ba65-475d-96c5-f2855f431028",
              "type": "TestCaseReport",
              "logs": [],
              "tags": {
                "colour": ["white"]
              },
              "timer": {
                "run": {
                  "start": "2018-10-15T14:30:11.010072+00:00",
                  "end": "2018-10-15T14:30:11.132214+00:00"
                }
              },
              "entries": [
                {
                  "category": "DEFAULT",
                  "machine_time": "2018-10-15T15:30:11.010098+00:00",
                  "description": "passing equality",
                  "line_no": 24,
                  "label": "==",
                  "second": 1,
                  "meta_type": "assertion",
                  "passed": true,
                  "type": "Equal",
                  "utc_time": "2018-10-15T14:30:11.010094+00:00",
                  "first": 1
                }
              ],
            },
            {
              "name": "test_equality_passing2",
              "category": "testcase",
              "status": "failed",
              "tags": {},
              "status_override": null,
              "description": null,
              "uid": "78686a4d-7b94-4ae6-ab50-d9960a7fb714",
              "type": "TestCaseReport",
              "logs": [],
              "timer": {
                "run": {
                  "start": "2018-10-15T14:30:11.510072+00:00",
                  "end": "2018-10-15T14:30:11.632214+00:00"
                }
              },
              "entries": [
                {
                  "category": "DEFAULT",
                  "machine_time": "2018-10-15T15:30:11.510098+00:00",
                  "description": "passing equality",
                  "line_no": 24,
                  "label": "==",
                  "second": 1,
                  "meta_type": "assertion",
                  "passed": true,
                  "type": "Equal",
                  "utc_time": "2018-10-15T14:30:11.510094+00:00",
                  "first": 1
                }
              ],
            },
          ],
        },
        {
          "status": "passed",
          "category": "testsuite",
          "name": "BetaSuite",
          "status_override": null,
          "description": null,
          "uid": "6fc5c008-4d1a-454e-80b6-74bdc9bca49e",
          "type": "TestGroupReport",
          "logs": [],
          "tags": {
            "simple": ["client"]
          },
          "timer": {
            "run": {
              "start": "2018-10-15T14:30:11.009872+00:00",
              "end": "2018-10-15T14:30:11.158224+00:00"
            }
          },
          "entries": [
            {
              "name": "test_equality_passing",
              "category": "testcase",
              "status": "passed",
              "tags": {},
              "status_override": null,
              "description": null,
              "uid": "8865a23d-1823-4c8d-ab37-58d24fc8ac05",
              "type": "TestCaseReport",
              "logs": [],
              "timer": {
                "run": {
                  "start": "2018-10-15T14:30:11.010072+00:00",
                  "end": "2018-10-15T14:30:11.132214+00:00"
                }
              },
              "entries": [
                {
                  "category": "DEFAULT",
                  "machine_time": "2018-10-15T15:30:11.010098+00:00",
                  "description": "passing equality",
                  "line_no": 24,
                  "label": "==",
                  "second": 1,
                  "meta_type": "assertion",
                  "passed": true,
                  "type": "Equal",
                  "utc_time": "2018-10-15T14:30:11.010094+00:00",
                  "first": 1
                }
              ],
            },
          ],
        },
      ],
    },
    {
      "name": "Secondary",
      "status": "passed",
      "category": "multitest",
      "tags": {},
      "description": null,
      "status_override": null,
      "uid": "8c3c7e6b-48e8-40cd-86db-8c8aed2592c8",
      "type": "TestGroupReport",
      "logs": [],
      "timer": {
        "run": {
          "start": "2018-10-15T14:30:12.009705+00:00",
          "end": "2018-10-15T14:30:12.159661+00:00"
        }
      },
      "entries": [
        {
          "status": "passed",
          "category": "testsuite",
          "name": "GammaSuite",
          "tags": {},
          "status_override": null,
          "description": null,
          "uid": "08d4c671-d55d-49d4-96ba-dc654d12be26",
          "type": "TestGroupReport",
          "logs": [],
          "timer": {
            "run": {
              "start": "2018-10-15T14:30:12.009872+00:00",
              "end": "2018-10-15T14:30:12.158224+00:00"
            }
          },
          "entries": [
            {
              "name": "test_equality_passing",
              "category": "testcase",
              "status": "passed",
              "tags": {},
              "status_override": null,
              "description": null,
              "uid": "f73bd6ea-d378-437b-a5db-00d9e427f36a",
              "type": "TestCaseReport",
              "logs": [],
              "timer": {
                "run": {
                  "start": "2018-10-15T14:30:12.010072+00:00",
                  "end": "2018-10-15T14:30:12.132214+00:00"
                }
              },
              "entries": [
                {
                  "category": "DEFAULT",
                  "machine_time": "2018-10-15T15:30:12.010098+00:00",
                  "description": "passing equality",
                  "line_no": 24,
                  "label": "==",
                  "second": 1,
                  "meta_type": "assertion",
                  "passed": true,
                  "type": "Equal",
                  "utc_time": "2018-10-15T14:30:12.010094+00:00",
                  "first": 1
                }
              ],
            },
          ],
        }
      ],
    },
  ],
};

var fakeReportAssertions = {
    "category": "testplan",
    "tags_index": {},
    "meta": {},
    "information": [
        [
            "user",
            "yifan"
        ],
        [
            "command_line_string",
            "oss/examples/Assertions/Basic/test_plan.py --json example.json"
        ],
        [
            "python_version",
            "3.7.1"
        ]
    ],
    "counter": {
        "passed": 2,
        "failed": 6,
        "total": 8
    },
    "uid": "c648a283-22f3-4503-ae6d-c982b4c7cca0",
    "attachments": {},
    "status": "failed",
    "timer": {
        "run": {
            "end": "2020-01-10T03:06:59.348924+00:00",
            "start": "2020-01-10T03:06:58.537339+00:00"
        }
    },
    "runtime_status": "finished",
    "name": "Assertions Example",
    "status_override": null,
    "entries": [
        {
            "description": null,
            "counter": {
                "passed": 2,
                "failed": 6,
                "total": 8
            },
            "name": "Assertions Test",
            "tags": {},
            "env_status": "STOPPED",
            "type": "TestGroupReport",
            "status_reason": null,
            "runtime_status": "finished",
            "fix_spec_path": null,
            "part": null,
            "uid": "99aef9f5-6957-4842-a6fa-e0cd9e358473",
            "status": "failed",
            "parent_uids": [
                "Assertions Example"
            ],
            "timer": {
                "run": {
                    "end": "2020-01-10T03:06:59.141338+00:00",
                    "start": "2020-01-10T03:06:58.629871+00:00"
                }
            },
            "hash": 3697482064019099674,
            "status_override": null,
            "logs": [],
            "category": "multitest",
            "entries": [
                {
                    "description": null,
                    "counter": {
                        "passed": 2,
                        "failed": 6,
                        "total": 8
                    },
                    "name": "SampleSuite",
                    "tags": {},
                    "env_status": null,
                    "type": "TestGroupReport",
                    "status_reason": null,
                    "runtime_status": "finished",
                    "fix_spec_path": null,
                    "part": null,
                    "uid": "9f98c732-d040-4a13-84e1-563adcd9dd32",
                    "status": "failed",
                    "parent_uids": [
                        "Assertions Example",
                        "Assertions Test"
                    ],
                    "timer": {
                        "run": {
                            "end": "2020-01-10T03:06:59.135813+00:00",
                            "start": "2020-01-10T03:06:58.629972+00:00"
                        }
                    },
                    "hash": -4958192469702756289,
                    "status_override": null,
                    "logs": [],
                    "category": "testsuite",
                    "entries": [
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": "Description test\nSecond description",
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "25d0115f-91c4-481b-ad0f-37382d95fabd",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:58.939142+00:00",
                                    "start": "2020-01-10T03:06:58.630091+00:00"
                                }
                            },
                            "hash": 4069384282795794238,
                            "runtime_status": "finished",
                            "name": "test_basic_assertions",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "==",
                                    "type": "Equal",
                                    "utc_time": "2020-01-10T03:06:58.630121+00:00",
                                    "second": "foo",
                                    "passed": true,
                                    "first": "foo",
                                    "machine_time": "2020-01-10T11:06:58.630129+00:00",
                                    "line_no": 25
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Description for failing equality",
                                    "meta_type": "assertion",
                                    "label": "==",
                                    "type": "Equal",
                                    "utc_time": "2020-01-10T03:06:58.893461+00:00",
                                    "second": 2,
                                    "passed": false,
                                    "first": 1,
                                    "machine_time": "2020-01-10T11:06:58.893477+00:00",
                                    "line_no": 28
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "!=",
                                    "type": "NotEqual",
                                    "utc_time": "2020-01-10T03:06:58.895795+00:00",
                                    "second": "bar",
                                    "passed": true,
                                    "first": "foo",
                                    "machine_time": "2020-01-10T11:06:58.895806+00:00",
                                    "line_no": 30
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": ">",
                                    "type": "Greater",
                                    "utc_time": "2020-01-10T03:06:58.898075+00:00",
                                    "second": 2,
                                    "passed": true,
                                    "first": 5,
                                    "machine_time": "2020-01-10T11:06:58.898084+00:00",
                                    "line_no": 31
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": ">=",
                                    "type": "GreaterEqual",
                                    "utc_time": "2020-01-10T03:06:58.899619+00:00",
                                    "second": 2,
                                    "passed": true,
                                    "first": 2,
                                    "machine_time": "2020-01-10T11:06:58.899627+00:00",
                                    "line_no": 32
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": ">=",
                                    "type": "GreaterEqual",
                                    "utc_time": "2020-01-10T03:06:58.901156+00:00",
                                    "second": 1,
                                    "passed": true,
                                    "first": 2,
                                    "machine_time": "2020-01-10T11:06:58.901163+00:00",
                                    "line_no": 33
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "<",
                                    "type": "Less",
                                    "utc_time": "2020-01-10T03:06:58.902604+00:00",
                                    "second": 20,
                                    "passed": true,
                                    "first": 10,
                                    "machine_time": "2020-01-10T11:06:58.902613+00:00",
                                    "line_no": 34
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "<=",
                                    "type": "LessEqual",
                                    "utc_time": "2020-01-10T03:06:58.904109+00:00",
                                    "second": 10,
                                    "passed": true,
                                    "first": 10,
                                    "machine_time": "2020-01-10T11:06:58.904117+00:00",
                                    "line_no": 35
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "<=",
                                    "type": "LessEqual",
                                    "utc_time": "2020-01-10T03:06:58.905543+00:00",
                                    "second": 30,
                                    "passed": true,
                                    "first": 10,
                                    "machine_time": "2020-01-10T11:06:58.905550+00:00",
                                    "line_no": 36
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "==",
                                    "type": "Equal",
                                    "utc_time": "2020-01-10T03:06:58.906994+00:00",
                                    "second": 15,
                                    "passed": true,
                                    "first": 15,
                                    "machine_time": "2020-01-10T11:06:58.907002+00:00",
                                    "line_no": 41
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "!=",
                                    "type": "NotEqual",
                                    "utc_time": "2020-01-10T03:06:58.908433+00:00",
                                    "second": 20,
                                    "passed": true,
                                    "first": 10,
                                    "machine_time": "2020-01-10T11:06:58.908440+00:00",
                                    "line_no": 42
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "<",
                                    "type": "Less",
                                    "utc_time": "2020-01-10T03:06:58.909946+00:00",
                                    "second": 3,
                                    "passed": true,
                                    "first": 2,
                                    "machine_time": "2020-01-10T11:06:58.909954+00:00",
                                    "line_no": 43
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": ">",
                                    "type": "Greater",
                                    "utc_time": "2020-01-10T03:06:58.911441+00:00",
                                    "second": 2,
                                    "passed": true,
                                    "first": 3,
                                    "machine_time": "2020-01-10T11:06:58.911449+00:00",
                                    "line_no": 44
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": "<=",
                                    "type": "LessEqual",
                                    "utc_time": "2020-01-10T03:06:58.912920+00:00",
                                    "second": 15,
                                    "passed": true,
                                    "first": 10,
                                    "machine_time": "2020-01-10T11:06:58.912928+00:00",
                                    "line_no": 45
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "label": ">=",
                                    "type": "GreaterEqual",
                                    "utc_time": "2020-01-10T03:06:58.914465+00:00",
                                    "second": 10,
                                    "passed": true,
                                    "first": 15,
                                    "machine_time": "2020-01-10T11:06:58.914473+00:00",
                                    "line_no": 46
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "rel_tol": 0.1,
                                    "label": "~=",
                                    "type": "IsClose",
                                    "utc_time": "2020-01-10T03:06:58.915976+00:00",
                                    "second": 95,
                                    "abs_tol": 0.0,
                                    "passed": true,
                                    "first": 100,
                                    "machine_time": "2020-01-10T11:06:58.915984+00:00",
                                    "line_no": 50
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "rel_tol": 0.01,
                                    "label": "~=",
                                    "type": "IsClose",
                                    "utc_time": "2020-01-10T03:06:58.917481+00:00",
                                    "second": 95,
                                    "abs_tol": 0.0,
                                    "passed": false,
                                    "first": 100,
                                    "machine_time": "2020-01-10T11:06:58.917489+00:00",
                                    "line_no": 51
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "entry",
                                    "type": "Log",
                                    "utc_time": "2020-01-10T03:06:58.919181+00:00",
                                    "machine_time": "2020-01-10T11:06:58.919189+00:00",
                                    "line_no": 56,
                                    "message": "This is a log message, it will be displayed along with other assertion details."
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Boolean Truthiness check",
                                    "meta_type": "assertion",
                                    "type": "IsTrue",
                                    "utc_time": "2020-01-10T03:06:58.921013+00:00",
                                    "expr": true,
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:58.921021+00:00",
                                    "line_no": 61
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Boolean Falseness check",
                                    "meta_type": "assertion",
                                    "type": "IsFalse",
                                    "utc_time": "2020-01-10T03:06:58.923056+00:00",
                                    "expr": false,
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:58.923064+00:00",
                                    "line_no": 62
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "This is an explicit failure.",
                                    "meta_type": "assertion",
                                    "type": "Fail",
                                    "utc_time": "2020-01-10T03:06:58.924595+00:00",
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:58.924621+00:00",
                                    "line_no": 64
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Passing membership",
                                    "meta_type": "assertion",
                                    "type": "Contain",
                                    "utc_time": "2020-01-10T03:06:58.926405+00:00",
                                    "container": "foobar",
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:58.926413+00:00",
                                    "line_no": 67,
                                    "member": "foo"
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Failing membership",
                                    "meta_type": "assertion",
                                    "type": "NotContain",
                                    "utc_time": "2020-01-10T03:06:58.928507+00:00",
                                    "container": "{'a': 1, 'b': 2}",
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:58.928515+00:00",
                                    "line_no": 71,
                                    "member": 10
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Comparison of slices",
                                    "meta_type": "assertion",
                                    "type": "EqualSlices",
                                    "utc_time": "2020-01-10T03:06:58.930479+00:00",
                                    "data": [
                                        [
                                            "slice(2, 4, None)",
                                            [
                                                2,
                                                3
                                            ],
                                            [],
                                            [
                                                3,
                                                4
                                            ],
                                            [
                                                3,
                                                4
                                            ]
                                        ],
                                        [
                                            "slice(6, 8, None)",
                                            [
                                                6,
                                                7
                                            ],
                                            [],
                                            [
                                                7,
                                                8
                                            ],
                                            [
                                                7,
                                                8
                                            ]
                                        ]
                                    ],
                                    "passed": true,
                                    "included_indices": [],
                                    "machine_time": "2020-01-10T11:06:58.930488+00:00",
                                    "expected": [
                                        "a",
                                        "b",
                                        3,
                                        4,
                                        "c",
                                        "d",
                                        7,
                                        8
                                    ],
                                    "line_no": 79,
                                    "actual": [
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                        6,
                                        7,
                                        8
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Comparison of slices (exclusion)",
                                    "meta_type": "assertion",
                                    "type": "EqualExcludeSlices",
                                    "utc_time": "2020-01-10T03:06:58.932694+00:00",
                                    "data": [
                                        [
                                            "slice(0, 2, None)",
                                            [
                                                2,
                                                3,
                                                4,
                                                5,
                                                6,
                                                7
                                            ],
                                            [
                                                4,
                                                5,
                                                6,
                                                7
                                            ],
                                            [
                                                3,
                                                4,
                                                5,
                                                6,
                                                7,
                                                8
                                            ],
                                            [
                                                3,
                                                4,
                                                "c",
                                                "d",
                                                "e",
                                                "f"
                                            ]
                                        ],
                                        [
                                            "slice(4, 8, None)",
                                            [
                                                0,
                                                1,
                                                2,
                                                3
                                            ],
                                            [
                                                0,
                                                1
                                            ],
                                            [
                                                1,
                                                2,
                                                3,
                                                4
                                            ],
                                            [
                                                "a",
                                                "b",
                                                3,
                                                4
                                            ]
                                        ]
                                    ],
                                    "passed": true,
                                    "included_indices": [
                                        2,
                                        3
                                    ],
                                    "machine_time": "2020-01-10T11:06:58.932703+00:00",
                                    "expected": [
                                        "a",
                                        "b",
                                        3,
                                        4,
                                        "c",
                                        "d",
                                        "e",
                                        "f"
                                    ],
                                    "line_no": 91,
                                    "actual": [
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                        6,
                                        7,
                                        8
                                    ]
                                },
                                {
                                    "unified": false,
                                    "category": "DEFAULT",
                                    "ignore_blank_lines": true,
                                    "description": null,
                                    "meta_type": "assertion",
                                    "type": "LineDiff",
                                    "utc_time": "2020-01-10T03:06:58.934779+00:00",
                                    "delta": [],
                                    "second": [
                                        "abc\n",
                                        "xyz\n",
                                        "\n"
                                    ],
                                    "context": false,
                                    "passed": true,
                                    "first": [
                                        "abc\n",
                                        "xyz\n"
                                    ],
                                    "machine_time": "2020-01-10T11:06:58.934786+00:00",
                                    "ignore_space_change": false,
                                    "line_no": 98,
                                    "ignore_whitespaces": false
                                },
                                {
                                    "unified": 3,
                                    "category": "DEFAULT",
                                    "ignore_blank_lines": false,
                                    "description": null,
                                    "meta_type": "assertion",
                                    "type": "LineDiff",
                                    "utc_time": "2020-01-10T03:06:58.936975+00:00",
                                    "delta": [],
                                    "second": [
                                        "1\n",
                                        "1\n",
                                        "1\n",
                                        "abc \n",
                                        "xy\t\tz\n",
                                        "2\n",
                                        "2\n",
                                        "2\n"
                                    ],
                                    "context": false,
                                    "passed": true,
                                    "first": [
                                        "1\r\n",
                                        "1\r\n",
                                        "1\r\n",
                                        "abc\r\n",
                                        "xy z\r\n",
                                        "2\r\n",
                                        "2\r\n",
                                        "2\r\n"
                                    ],
                                    "machine_time": "2020-01-10T11:06:58.936983+00:00",
                                    "ignore_space_change": true,
                                    "line_no": 102,
                                    "ignore_whitespaces": false
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 1,
                                "failed": 0,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "cd31b565-3702-4540-a140-ff9fd480e8ce",
                            "status": "passed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:58.963478+00:00",
                                    "start": "2020-01-10T03:06:58.954190+00:00"
                                }
                            },
                            "hash": -6066149844839810607,
                            "runtime_status": "finished",
                            "name": "test_raised_exceptions",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": null,
                                    "type": "ExceptionRaised",
                                    "utc_time": "2020-01-10T03:06:58.954270+00:00",
                                    "func_match": true,
                                    "raised_exception": [
                                        "<class 'KeyError'>",
                                        "'bar'"
                                    ],
                                    "exception_match": true,
                                    "expected_exceptions": [
                                        "KeyError"
                                    ],
                                    "passed": true,
                                    "pattern_match": true,
                                    "machine_time": "2020-01-10T11:06:58.954275+00:00",
                                    "func": null,
                                    "line_no": 112
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Exception raised with custom pattern.",
                                    "meta_type": "assertion",
                                    "pattern": "foobar",
                                    "type": "ExceptionRaised",
                                    "utc_time": "2020-01-10T03:06:58.955863+00:00",
                                    "func_match": true,
                                    "raised_exception": [
                                        "<class 'ValueError'>",
                                        "abc foobar xyz"
                                    ],
                                    "exception_match": true,
                                    "expected_exceptions": [
                                        "ValueError"
                                    ],
                                    "passed": true,
                                    "pattern_match": true,
                                    "machine_time": "2020-01-10T11:06:58.955871+00:00",
                                    "func": null,
                                    "line_no": 121
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Exception raised with custom func.",
                                    "meta_type": "assertion",
                                    "pattern": null,
                                    "type": "ExceptionRaised",
                                    "utc_time": "2020-01-10T03:06:58.957489+00:00",
                                    "func_match": true,
                                    "raised_exception": [
                                        "<class '__main__.SampleSuite.test_raised_exceptions.<locals>.MyException'>",
                                        "4"
                                    ],
                                    "exception_match": true,
                                    "expected_exceptions": [
                                        "MyException"
                                    ],
                                    "passed": true,
                                    "pattern_match": true,
                                    "machine_time": "2020-01-10T11:06:58.957497+00:00",
                                    "func": "<function SampleSuite.test_raised_exceptions.<locals>.custom_func at 0x7f9cfc64fea0>",
                                    "line_no": 139
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": null,
                                    "type": "ExceptionNotRaised",
                                    "utc_time": "2020-01-10T03:06:58.958956+00:00",
                                    "func_match": true,
                                    "raised_exception": [
                                        "<class 'KeyError'>",
                                        "'bar'"
                                    ],
                                    "exception_match": false,
                                    "expected_exceptions": [
                                        "TypeError"
                                    ],
                                    "passed": true,
                                    "pattern_match": true,
                                    "machine_time": "2020-01-10T11:06:58.958964+00:00",
                                    "func": null,
                                    "line_no": 146
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Exception not raised with custom pattern.",
                                    "meta_type": "assertion",
                                    "pattern": "foobar",
                                    "type": "ExceptionNotRaised",
                                    "utc_time": "2020-01-10T03:06:58.960503+00:00",
                                    "func_match": true,
                                    "raised_exception": [
                                        "<class 'ValueError'>",
                                        "abc"
                                    ],
                                    "exception_match": true,
                                    "expected_exceptions": [
                                        "ValueError"
                                    ],
                                    "passed": true,
                                    "pattern_match": null,
                                    "machine_time": "2020-01-10T11:06:58.960510+00:00",
                                    "func": null,
                                    "line_no": 157
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Exception not raised with custom func.",
                                    "meta_type": "assertion",
                                    "pattern": null,
                                    "type": "ExceptionNotRaised",
                                    "utc_time": "2020-01-10T03:06:58.962023+00:00",
                                    "func_match": false,
                                    "raised_exception": [
                                        "<class '__main__.SampleSuite.test_raised_exceptions.<locals>.MyException'>",
                                        "5"
                                    ],
                                    "exception_match": true,
                                    "expected_exceptions": [
                                        "MyException"
                                    ],
                                    "passed": true,
                                    "pattern_match": true,
                                    "machine_time": "2020-01-10T11:06:58.962031+00:00",
                                    "func": "<function SampleSuite.test_raised_exceptions.<locals>.custom_func at 0x7f9cfc64fea0>",
                                    "line_no": 165
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "fca0596d-c220-4267-9a38-57968aca92d5",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:58.979777+00:00",
                                    "start": "2020-01-10T03:06:58.971424+00:00"
                                }
                            },
                            "hash": -2707574492059523373,
                            "runtime_status": "finished",
                            "name": "test_assertion_group  -- very long long long long long long long longlong long long longlong long long long name",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": "Equality assertion outside the group",
                                    "meta_type": "assertion",
                                    "label": "==",
                                    "type": "Equal",
                                    "utc_time": "2020-01-10T03:06:58.971447+00:00",
                                    "second": 1,
                                    "passed": true,
                                    "first": 1,
                                    "machine_time": "2020-01-10T11:06:58.971451+00:00",
                                    "line_no": 173
                                },
                                {
                                    "description": "Custom group description",
                                    "meta_type": "assertion",
                                    "type": "Group",
                                    "passed": false,
                                    "entries": [
                                        {
                                            "category": "DEFAULT",
                                            "description": "Assertion within a group",
                                            "meta_type": "assertion",
                                            "label": "!=",
                                            "type": "NotEqual",
                                            "utc_time": "2020-01-10T03:06:58.973038+00:00",
                                            "second": 3,
                                            "passed": true,
                                            "first": 2,
                                            "machine_time": "2020-01-10T11:06:58.973047+00:00",
                                            "line_no": 176
                                        },
                                        {
                                            "category": "DEFAULT",
                                            "description": null,
                                            "meta_type": "assertion",
                                            "label": ">",
                                            "type": "Greater",
                                            "utc_time": "2020-01-10T03:06:58.974577+00:00",
                                            "second": 3,
                                            "passed": true,
                                            "first": 5,
                                            "machine_time": "2020-01-10T11:06:58.974586+00:00",
                                            "line_no": 177
                                        },
                                        {
                                            "description": "This is a sub group",
                                            "meta_type": "assertion",
                                            "type": "Group",
                                            "passed": false,
                                            "entries": [
                                                {
                                                    "category": "DEFAULT",
                                                    "description": "Assertion within sub group",
                                                    "meta_type": "assertion",
                                                    "label": "<",
                                                    "type": "Less",
                                                    "utc_time": "2020-01-10T03:06:58.976376+00:00",
                                                    "second": 3,
                                                    "passed": false,
                                                    "first": 6,
                                                    "machine_time": "2020-01-10T11:06:58.976384+00:00",
                                                    "line_no": 181
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Final assertion outside all groups",
                                    "meta_type": "assertion",
                                    "label": "==",
                                    "type": "Equal",
                                    "utc_time": "2020-01-10T03:06:58.978219+00:00",
                                    "second": "foo",
                                    "passed": true,
                                    "first": "foo",
                                    "machine_time": "2020-01-10T11:06:58.978227+00:00",
                                    "line_no": 184
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "a3fd1023-b150-487a-bc7d-c0f64e326e63",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:59.006101+00:00",
                                    "start": "2020-01-10T03:06:58.987035+00:00"
                                }
                            },
                            "hash": -8719069130512673532,
                            "runtime_status": "finished",
                            "name": "test_regex_namespace",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": "string pattern match",
                                    "meta_type": "assertion",
                                    "pattern": "foo",
                                    "type": "RegexMatch",
                                    "utc_time": "2020-01-10T03:06:58.987140+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            3
                                        ]
                                    ],
                                    "passed": true,
                                    "string": "foobar",
                                    "machine_time": "2020-01-10T11:06:58.987146+00:00",
                                    "line_no": 196
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "SRE match",
                                    "meta_type": "assertion",
                                    "pattern": "foo",
                                    "type": "RegexMatch",
                                    "utc_time": "2020-01-10T03:06:58.988905+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            3
                                        ]
                                    ],
                                    "passed": true,
                                    "string": "foobar",
                                    "machine_time": "2020-01-10T11:06:58.988913+00:00",
                                    "line_no": 201
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "first line.*second",
                                    "type": "RegexMatch",
                                    "utc_time": "2020-01-10T03:06:58.991277+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            17
                                        ]
                                    ],
                                    "passed": true,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:58.991285+00:00",
                                    "line_no": 212
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "baz",
                                    "type": "RegexMatchNotExists",
                                    "utc_time": "2020-01-10T03:06:58.992937+00:00",
                                    "match_indexes": [],
                                    "passed": true,
                                    "string": "foobar",
                                    "machine_time": "2020-01-10T11:06:58.992945+00:00",
                                    "line_no": 217
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "foobar",
                                    "type": "RegexMatchNotExists",
                                    "utc_time": "2020-01-10T03:06:58.994520+00:00",
                                    "match_indexes": [],
                                    "passed": true,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:58.994527+00:00",
                                    "line_no": 222
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "second",
                                    "type": "RegexSearch",
                                    "utc_time": "2020-01-10T03:06:58.996148+00:00",
                                    "match_indexes": [
                                        [
                                            11,
                                            17
                                        ]
                                    ],
                                    "passed": true,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:58.996156+00:00",
                                    "line_no": 225
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Passing search empty",
                                    "meta_type": "assertion",
                                    "pattern": "foobar",
                                    "type": "RegexSearchNotExists",
                                    "utc_time": "2020-01-10T03:06:58.997760+00:00",
                                    "match_indexes": [],
                                    "passed": true,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:58.997768+00:00",
                                    "line_no": 230
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Failing search_empty",
                                    "meta_type": "assertion",
                                    "pattern": "second",
                                    "type": "RegexSearchNotExists",
                                    "utc_time": "2020-01-10T03:06:58.999296+00:00",
                                    "match_indexes": [
                                        [
                                            11,
                                            17
                                        ]
                                    ],
                                    "passed": false,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:58.999303+00:00",
                                    "line_no": 233
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "foo",
                                    "type": "RegexFindIter",
                                    "utc_time": "2020-01-10T03:06:59.000852+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            3
                                        ],
                                        [
                                            4,
                                            7
                                        ],
                                        [
                                            8,
                                            11
                                        ],
                                        [
                                            20,
                                            23
                                        ]
                                    ],
                                    "condition": "<lambda>",
                                    "passed": true,
                                    "string": "foo foo foo bar bar foo bar",
                                    "machine_time": "2020-01-10T11:06:59.000860+00:00",
                                    "condition_match": true,
                                    "line_no": 243
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "foo",
                                    "type": "RegexFindIter",
                                    "utc_time": "2020-01-10T03:06:59.002669+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            3
                                        ],
                                        [
                                            4,
                                            7
                                        ],
                                        [
                                            8,
                                            11
                                        ],
                                        [
                                            20,
                                            23
                                        ]
                                    ],
                                    "condition": "(VAL > 2 and VAL < 5)",
                                    "passed": true,
                                    "string": "foo foo foo bar bar foo bar",
                                    "machine_time": "2020-01-10T11:06:59.002676+00:00",
                                    "condition_match": true,
                                    "line_no": 250
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "pattern": "\\w+ line$",
                                    "type": "RegexMatchLine",
                                    "utc_time": "2020-01-10T03:06:59.004622+00:00",
                                    "match_indexes": [
                                        [
                                            0,
                                            0,
                                            10
                                        ],
                                        [
                                            1,
                                            0,
                                            11
                                        ],
                                        [
                                            2,
                                            0,
                                            10
                                        ]
                                    ],
                                    "passed": true,
                                    "string": "first line\nsecond line\nthird line",
                                    "machine_time": "2020-01-10T11:06:59.004630+00:00",
                                    "line_no": 257
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "e8fb2848-cc83-4df3-83e0-82fe839d6526",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:59.072704+00:00",
                                    "start": "2020-01-10T03:06:59.016322+00:00"
                                }
                            },
                            "hash": -8829886055223884393,
                            "runtime_status": "finished",
                            "name": "test_table_namespace",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: list of list vs list of list",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.016418+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                "Bob",
                                                32
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            1,
                                            [
                                                "Susan",
                                                24
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {},
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.016424+00:00",
                                    "line_no": 284,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: list of dict vs list of dict",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.018525+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                "Bob",
                                                32
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            1,
                                            [
                                                "Susan",
                                                24
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {},
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.018533+00:00",
                                    "line_no": 289,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: list of dict vs list of list",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.020629+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                "Bob",
                                                32
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            1,
                                            [
                                                "Susan",
                                                24
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {},
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.020640+00:00",
                                    "line_no": 294,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: list of list vs list of list",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.023695+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [],
                                    "report_fails_only": true,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.023703+00:00",
                                    "line_no": 299,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: list of dict vs list of dict",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.026093+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [],
                                    "report_fails_only": true,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.026102+00:00",
                                    "line_no": 304,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: list of dict vs list of list",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.027835+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [],
                                    "report_fails_only": true,
                                    "passed": true,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.027843+00:00",
                                    "line_no": 309,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: simple comparators",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.029541+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                "Bob",
                                                32
                                            ],
                                            {},
                                            {},
                                            {
                                                "name": "REGEX(\\w{3})",
                                                "age": "<lambda>"
                                            }
                                        ],
                                        [
                                            1,
                                            [
                                                "Susan",
                                                24
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {
                                                "name": "<lambda>"
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.029549+00:00",
                                    "line_no": 338,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: simple comparators",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.031666+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {
                                                "name": "<lambda>"
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": true,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.031674+00:00",
                                    "line_no": 343,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: readable comparators",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.034598+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                "Bob",
                                                32
                                            ],
                                            {},
                                            {},
                                            {
                                                "name": "REGEX(\\w{3})",
                                                "age": "(VAL > 30 and VAL < 40)"
                                            }
                                        ],
                                        [
                                            1,
                                            [
                                                "Susan",
                                                24
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {
                                                "name": "VAL in ['David', 'Helen', 'Pablo']"
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.034625+00:00",
                                    "line_no": 361,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: readable comparators",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.037495+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "data": [
                                        [
                                            2,
                                            [
                                                "Rick",
                                                67
                                            ],
                                            {
                                                "name": "VAL in ['David', 'Helen', 'Pablo']"
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": true,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.037502+00:00",
                                    "line_no": 366,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: Trimmed columns",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.040045+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "column_1",
                                        "column_2"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                0,
                                                0
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            1,
                                            [
                                                1,
                                                2
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                2,
                                                4
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            3,
                                            [
                                                3,
                                                6
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            4,
                                            [
                                                4,
                                                8
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            5,
                                            [
                                                5,
                                                10
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            6,
                                            [
                                                6,
                                                12
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            7,
                                            [
                                                7,
                                                14
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            8,
                                            [
                                                8,
                                                16
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            9,
                                            [
                                                9,
                                                18
                                            ],
                                            {},
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": true,
                                    "include_columns": [
                                        "column_1",
                                        "column_2"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.040052+00:00",
                                    "line_no": 383,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: Trimmed columns",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.042860+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 0,
                                    "columns": [
                                        "column_1",
                                        "column_2"
                                    ],
                                    "data": [],
                                    "report_fails_only": true,
                                    "passed": true,
                                    "include_columns": [
                                        "column_1",
                                        "column_2"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.042869+00:00",
                                    "line_no": 391,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Match: Trimmed rows",
                                    "meta_type": "assertion",
                                    "type": "TableMatch",
                                    "utc_time": "2020-01-10T03:06:59.046590+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 2,
                                    "columns": [
                                        "amount",
                                        "product_id"
                                    ],
                                    "data": [
                                        [
                                            0,
                                            [
                                                0,
                                                4240
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            1,
                                            [
                                                10,
                                                3961
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            2,
                                            [
                                                20,
                                                1627
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            3,
                                            [
                                                30,
                                                1351
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            4,
                                            [
                                                40,
                                                2123
                                            ],
                                            {},
                                            {},
                                            {}
                                        ],
                                        [
                                            5,
                                            [
                                                25,
                                                1111
                                            ],
                                            {
                                                "amount": 35
                                            },
                                            {},
                                            {}
                                        ],
                                        [
                                            6,
                                            [
                                                20,
                                                2222
                                            ],
                                            {
                                                "product_id": 1234
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": false,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.046598+00:00",
                                    "line_no": 428,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Diff: Trimmed rows",
                                    "meta_type": "assertion",
                                    "type": "TableDiff",
                                    "utc_time": "2020-01-10T03:06:59.049590+00:00",
                                    "exclude_columns": null,
                                    "fail_limit": 2,
                                    "columns": [
                                        "amount",
                                        "product_id"
                                    ],
                                    "data": [
                                        [
                                            5,
                                            [
                                                25,
                                                1111
                                            ],
                                            {
                                                "amount": 35
                                            },
                                            {},
                                            {}
                                        ],
                                        [
                                            6,
                                            [
                                                20,
                                                2222
                                            ],
                                            {
                                                "product_id": 1234
                                            },
                                            {},
                                            {}
                                        ]
                                    ],
                                    "report_fails_only": true,
                                    "passed": false,
                                    "include_columns": null,
                                    "machine_time": "2020-01-10T11:06:59.049598+00:00",
                                    "line_no": 437,
                                    "message": null,
                                    "strict": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "column": "symbol",
                                    "limit": null,
                                    "type": "ColumnContain",
                                    "utc_time": "2020-01-10T03:06:59.051390+00:00",
                                    "data": [
                                        [
                                            0,
                                            "AAPL",
                                            true
                                        ],
                                        [
                                            1,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            2,
                                            "FB",
                                            false
                                        ],
                                        [
                                            3,
                                            "AMZN",
                                            true
                                        ],
                                        [
                                            4,
                                            "MSFT",
                                            false
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.051397+00:00",
                                    "values": [
                                        "AAPL",
                                        "AMZN"
                                    ],
                                    "line_no": 454,
                                    "report_fails_only": false
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "column": "symbol",
                                    "limit": 20,
                                    "type": "ColumnContain",
                                    "utc_time": "2020-01-10T03:06:59.057037+00:00",
                                    "data": [
                                        [
                                            1,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            2,
                                            "FB",
                                            false
                                        ],
                                        [
                                            4,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            6,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            7,
                                            "FB",
                                            false
                                        ],
                                        [
                                            9,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            11,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            12,
                                            "FB",
                                            false
                                        ],
                                        [
                                            14,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            16,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            17,
                                            "FB",
                                            false
                                        ],
                                        [
                                            19,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            21,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            22,
                                            "FB",
                                            false
                                        ],
                                        [
                                            24,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            26,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            27,
                                            "FB",
                                            false
                                        ],
                                        [
                                            29,
                                            "MSFT",
                                            false
                                        ],
                                        [
                                            31,
                                            "GOOG",
                                            false
                                        ],
                                        [
                                            32,
                                            "FB",
                                            false
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.057048+00:00",
                                    "values": [
                                        "AAPL",
                                        "AMZN"
                                    ],
                                    "line_no": 467,
                                    "report_fails_only": true
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Log: list of dicts",
                                    "meta_type": "entry",
                                    "type": "TableLog",
                                    "utc_time": "2020-01-10T03:06:59.060012+00:00",
                                    "table": [
                                        {
                                            "name": "Bob",
                                            "age": 32
                                        },
                                        {
                                            "name": "Susan",
                                            "age": 24
                                        },
                                        {
                                            "name": "Rick",
                                            "age": 67
                                        }
                                    ],
                                    "display_index": false,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.060020+00:00",
                                    "line_no": 472,
                                    "indices": [
                                        0,
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Log: list of lists",
                                    "meta_type": "entry",
                                    "type": "TableLog",
                                    "utc_time": "2020-01-10T03:06:59.061711+00:00",
                                    "table": [
                                        {
                                            "name": "Bob",
                                            "age": 32
                                        },
                                        {
                                            "name": "Susan",
                                            "age": 24
                                        },
                                        {
                                            "name": "Rick",
                                            "age": 67
                                        }
                                    ],
                                    "display_index": false,
                                    "columns": [
                                        "name",
                                        "age"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.061718+00:00",
                                    "line_no": 473,
                                    "indices": [
                                        0,
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Log: many rows",
                                    "meta_type": "entry",
                                    "type": "TableLog",
                                    "utc_time": "2020-01-10T03:06:59.063421+00:00",
                                    "table": [
                                        {
                                            "symbol": "AAPL",
                                            "amount": 12
                                        },
                                        {
                                            "symbol": "GOOG",
                                            "amount": 21
                                        },
                                        {
                                            "symbol": "FB",
                                            "amount": 32
                                        },
                                        {
                                            "symbol": "AMZN",
                                            "amount": 5
                                        },
                                        {
                                            "symbol": "MSFT",
                                            "amount": 42
                                        },
                                        {
                                            "symbol": "AAPL",
                                            "amount": 12
                                        },
                                        {
                                            "symbol": "GOOG",
                                            "amount": 21
                                        },
                                        {
                                            "symbol": "FB",
                                            "amount": 32
                                        },
                                        {
                                            "symbol": "AMZN",
                                            "amount": 5
                                        },
                                        {
                                            "symbol": "MSFT",
                                            "amount": 42
                                        },
                                        {
                                            "symbol": "AAPL",
                                            "amount": 12
                                        },
                                        {
                                            "symbol": "GOOG",
                                            "amount": 21
                                        },
                                        {
                                            "symbol": "FB",
                                            "amount": 32
                                        },
                                        {
                                            "symbol": "AMZN",
                                            "amount": 5
                                        },
                                        {
                                            "symbol": "MSFT",
                                            "amount": 42
                                        },
                                        {
                                            "symbol": "AAPL",
                                            "amount": 12
                                        },
                                        {
                                            "symbol": "GOOG",
                                            "amount": 21
                                        },
                                        {
                                            "symbol": "FB",
                                            "amount": 32
                                        },
                                        {
                                            "symbol": "AMZN",
                                            "amount": 5
                                        },
                                        {
                                            "symbol": "MSFT",
                                            "amount": 42
                                        }
                                    ],
                                    "display_index": false,
                                    "columns": [
                                        "symbol",
                                        "amount"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.063429+00:00",
                                    "line_no": 479,
                                    "indices": [
                                        0,
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                        6,
                                        7,
                                        8,
                                        9,
                                        10,
                                        11,
                                        12,
                                        13,
                                        14,
                                        15,
                                        16,
                                        17,
                                        18,
                                        19
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Log: many columns",
                                    "meta_type": "entry",
                                    "type": "TableLog",
                                    "utc_time": "2020-01-10T03:06:59.065884+00:00",
                                    "table": [
                                        {
                                            "col_0": "row 0 col 0",
                                            "col_1": "row 0 col 1",
                                            "col_2": "row 0 col 2",
                                            "col_3": "row 0 col 3",
                                            "col_4": "row 0 col 4",
                                            "col_5": "row 0 col 5",
                                            "col_6": "row 0 col 6",
                                            "col_7": "row 0 col 7",
                                            "col_8": "row 0 col 8",
                                            "col_9": "row 0 col 9",
                                            "col_10": "row 0 col 10",
                                            "col_11": "row 0 col 11",
                                            "col_12": "row 0 col 12",
                                            "col_13": "row 0 col 13",
                                            "col_14": "row 0 col 14",
                                            "col_15": "row 0 col 15",
                                            "col_16": "row 0 col 16",
                                            "col_17": "row 0 col 17",
                                            "col_18": "row 0 col 18",
                                            "col_19": "row 0 col 19"
                                        },
                                        {
                                            "col_0": "row 1 col 0",
                                            "col_1": "row 1 col 1",
                                            "col_2": "row 1 col 2",
                                            "col_3": "row 1 col 3",
                                            "col_4": "row 1 col 4",
                                            "col_5": "row 1 col 5",
                                            "col_6": "row 1 col 6",
                                            "col_7": "row 1 col 7",
                                            "col_8": "row 1 col 8",
                                            "col_9": "row 1 col 9",
                                            "col_10": "row 1 col 10",
                                            "col_11": "row 1 col 11",
                                            "col_12": "row 1 col 12",
                                            "col_13": "row 1 col 13",
                                            "col_14": "row 1 col 14",
                                            "col_15": "row 1 col 15",
                                            "col_16": "row 1 col 16",
                                            "col_17": "row 1 col 17",
                                            "col_18": "row 1 col 18",
                                            "col_19": "row 1 col 19"
                                        },
                                        {
                                            "col_0": "row 2 col 0",
                                            "col_1": "row 2 col 1",
                                            "col_2": "row 2 col 2",
                                            "col_3": "row 2 col 3",
                                            "col_4": "row 2 col 4",
                                            "col_5": "row 2 col 5",
                                            "col_6": "row 2 col 6",
                                            "col_7": "row 2 col 7",
                                            "col_8": "row 2 col 8",
                                            "col_9": "row 2 col 9",
                                            "col_10": "row 2 col 10",
                                            "col_11": "row 2 col 11",
                                            "col_12": "row 2 col 12",
                                            "col_13": "row 2 col 13",
                                            "col_14": "row 2 col 14",
                                            "col_15": "row 2 col 15",
                                            "col_16": "row 2 col 16",
                                            "col_17": "row 2 col 17",
                                            "col_18": "row 2 col 18",
                                            "col_19": "row 2 col 19"
                                        },
                                        {
                                            "col_0": "row 3 col 0",
                                            "col_1": "row 3 col 1",
                                            "col_2": "row 3 col 2",
                                            "col_3": "row 3 col 3",
                                            "col_4": "row 3 col 4",
                                            "col_5": "row 3 col 5",
                                            "col_6": "row 3 col 6",
                                            "col_7": "row 3 col 7",
                                            "col_8": "row 3 col 8",
                                            "col_9": "row 3 col 9",
                                            "col_10": "row 3 col 10",
                                            "col_11": "row 3 col 11",
                                            "col_12": "row 3 col 12",
                                            "col_13": "row 3 col 13",
                                            "col_14": "row 3 col 14",
                                            "col_15": "row 3 col 15",
                                            "col_16": "row 3 col 16",
                                            "col_17": "row 3 col 17",
                                            "col_18": "row 3 col 18",
                                            "col_19": "row 3 col 19"
                                        },
                                        {
                                            "col_0": "row 4 col 0",
                                            "col_1": "row 4 col 1",
                                            "col_2": "row 4 col 2",
                                            "col_3": "row 4 col 3",
                                            "col_4": "row 4 col 4",
                                            "col_5": "row 4 col 5",
                                            "col_6": "row 4 col 6",
                                            "col_7": "row 4 col 7",
                                            "col_8": "row 4 col 8",
                                            "col_9": "row 4 col 9",
                                            "col_10": "row 4 col 10",
                                            "col_11": "row 4 col 11",
                                            "col_12": "row 4 col 12",
                                            "col_13": "row 4 col 13",
                                            "col_14": "row 4 col 14",
                                            "col_15": "row 4 col 15",
                                            "col_16": "row 4 col 16",
                                            "col_17": "row 4 col 17",
                                            "col_18": "row 4 col 18",
                                            "col_19": "row 4 col 19"
                                        },
                                        {
                                            "col_0": "row 5 col 0",
                                            "col_1": "row 5 col 1",
                                            "col_2": "row 5 col 2",
                                            "col_3": "row 5 col 3",
                                            "col_4": "row 5 col 4",
                                            "col_5": "row 5 col 5",
                                            "col_6": "row 5 col 6",
                                            "col_7": "row 5 col 7",
                                            "col_8": "row 5 col 8",
                                            "col_9": "row 5 col 9",
                                            "col_10": "row 5 col 10",
                                            "col_11": "row 5 col 11",
                                            "col_12": "row 5 col 12",
                                            "col_13": "row 5 col 13",
                                            "col_14": "row 5 col 14",
                                            "col_15": "row 5 col 15",
                                            "col_16": "row 5 col 16",
                                            "col_17": "row 5 col 17",
                                            "col_18": "row 5 col 18",
                                            "col_19": "row 5 col 19"
                                        },
                                        {
                                            "col_0": "row 6 col 0",
                                            "col_1": "row 6 col 1",
                                            "col_2": "row 6 col 2",
                                            "col_3": "row 6 col 3",
                                            "col_4": "row 6 col 4",
                                            "col_5": "row 6 col 5",
                                            "col_6": "row 6 col 6",
                                            "col_7": "row 6 col 7",
                                            "col_8": "row 6 col 8",
                                            "col_9": "row 6 col 9",
                                            "col_10": "row 6 col 10",
                                            "col_11": "row 6 col 11",
                                            "col_12": "row 6 col 12",
                                            "col_13": "row 6 col 13",
                                            "col_14": "row 6 col 14",
                                            "col_15": "row 6 col 15",
                                            "col_16": "row 6 col 16",
                                            "col_17": "row 6 col 17",
                                            "col_18": "row 6 col 18",
                                            "col_19": "row 6 col 19"
                                        },
                                        {
                                            "col_0": "row 7 col 0",
                                            "col_1": "row 7 col 1",
                                            "col_2": "row 7 col 2",
                                            "col_3": "row 7 col 3",
                                            "col_4": "row 7 col 4",
                                            "col_5": "row 7 col 5",
                                            "col_6": "row 7 col 6",
                                            "col_7": "row 7 col 7",
                                            "col_8": "row 7 col 8",
                                            "col_9": "row 7 col 9",
                                            "col_10": "row 7 col 10",
                                            "col_11": "row 7 col 11",
                                            "col_12": "row 7 col 12",
                                            "col_13": "row 7 col 13",
                                            "col_14": "row 7 col 14",
                                            "col_15": "row 7 col 15",
                                            "col_16": "row 7 col 16",
                                            "col_17": "row 7 col 17",
                                            "col_18": "row 7 col 18",
                                            "col_19": "row 7 col 19"
                                        },
                                        {
                                            "col_0": "row 8 col 0",
                                            "col_1": "row 8 col 1",
                                            "col_2": "row 8 col 2",
                                            "col_3": "row 8 col 3",
                                            "col_4": "row 8 col 4",
                                            "col_5": "row 8 col 5",
                                            "col_6": "row 8 col 6",
                                            "col_7": "row 8 col 7",
                                            "col_8": "row 8 col 8",
                                            "col_9": "row 8 col 9",
                                            "col_10": "row 8 col 10",
                                            "col_11": "row 8 col 11",
                                            "col_12": "row 8 col 12",
                                            "col_13": "row 8 col 13",
                                            "col_14": "row 8 col 14",
                                            "col_15": "row 8 col 15",
                                            "col_16": "row 8 col 16",
                                            "col_17": "row 8 col 17",
                                            "col_18": "row 8 col 18",
                                            "col_19": "row 8 col 19"
                                        },
                                        {
                                            "col_0": "row 9 col 0",
                                            "col_1": "row 9 col 1",
                                            "col_2": "row 9 col 2",
                                            "col_3": "row 9 col 3",
                                            "col_4": "row 9 col 4",
                                            "col_5": "row 9 col 5",
                                            "col_6": "row 9 col 6",
                                            "col_7": "row 9 col 7",
                                            "col_8": "row 9 col 8",
                                            "col_9": "row 9 col 9",
                                            "col_10": "row 9 col 10",
                                            "col_11": "row 9 col 11",
                                            "col_12": "row 9 col 12",
                                            "col_13": "row 9 col 13",
                                            "col_14": "row 9 col 14",
                                            "col_15": "row 9 col 15",
                                            "col_16": "row 9 col 16",
                                            "col_17": "row 9 col 17",
                                            "col_18": "row 9 col 18",
                                            "col_19": "row 9 col 19"
                                        }
                                    ],
                                    "display_index": false,
                                    "columns": [
                                        "col_0",
                                        "col_1",
                                        "col_2",
                                        "col_3",
                                        "col_4",
                                        "col_5",
                                        "col_6",
                                        "col_7",
                                        "col_8",
                                        "col_9",
                                        "col_10",
                                        "col_11",
                                        "col_12",
                                        "col_13",
                                        "col_14",
                                        "col_15",
                                        "col_16",
                                        "col_17",
                                        "col_18",
                                        "col_19"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.065891+00:00",
                                    "line_no": 490,
                                    "indices": [
                                        0,
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                        6,
                                        7,
                                        8,
                                        9
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Table Log: long cells",
                                    "meta_type": "entry",
                                    "type": "TableLog",
                                    "utc_time": "2020-01-10T03:06:59.070773+00:00",
                                    "table": [
                                        {
                                            "Name": "Bob Stevens",
                                            "Age": "33",
                                            "Address": "89 Trinsdale Avenue, LONDON, E8 0XW"
                                        },
                                        {
                                            "Name": "Susan Evans",
                                            "Age": "21",
                                            "Address": "100 Loop Road, SWANSEA, U8 12JK"
                                        },
                                        {
                                            "Name": "Trevor Dune",
                                            "Age": "88",
                                            "Address": "28 Kings Lane, MANCHESTER, MT16 2YT"
                                        },
                                        {
                                            "Name": "Belinda Baggins",
                                            "Age": "38",
                                            "Address": "31 Prospect Hill, DOYNTON, BS30 9DN"
                                        },
                                        {
                                            "Name": "Cosimo Hornblower",
                                            "Age": "89",
                                            "Address": "65 Prospect Hill, SURREY, PH33 4TY"
                                        },
                                        {
                                            "Name": "Sabine Wurfel",
                                            "Age": "31",
                                            "Address": "88 Clasper Way, HEXWORTHY, PL20 4BG"
                                        }
                                    ],
                                    "display_index": false,
                                    "columns": [
                                        "Name",
                                        "Age",
                                        "Address"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.070780+00:00",
                                    "line_no": 504,
                                    "indices": [
                                        0,
                                        1,
                                        2,
                                        3,
                                        4,
                                        5
                                    ]
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "ca8979be-8eb3-4ff4-8c18-aba4c8348bac",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:59.102866+00:00",
                                    "start": "2020-01-10T03:06:59.087638+00:00"
                                }
                            },
                            "hash": -6007544999293600650,
                            "runtime_status": "finished",
                            "name": "test_dict_namespace",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": "Simple dict match",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.087672+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Passed",
                                            [
                                                "int",
                                                "1"
                                            ],
                                            [
                                                "int",
                                                "1"
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            "Failed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "int",
                                                "5"
                                            ]
                                        ],
                                        [
                                            0,
                                            "extra-key",
                                            "Failed",
                                            [
                                                null,
                                                "ABSENT"
                                            ],
                                            [
                                                "int",
                                                "10"
                                            ]
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.087677+00:00",
                                    "exclude_keys": null,
                                    "line_no": 524
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Nested dict match",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.089583+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            "alpha",
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            [
                                                "int",
                                                "1"
                                            ],
                                            [
                                                "int",
                                                "1"
                                            ]
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ],
                                        [
                                            1,
                                            "",
                                            "Failed",
                                            [
                                                "int",
                                                "3"
                                            ],
                                            [
                                                null,
                                                null
                                            ]
                                        ],
                                        [
                                            1,
                                            "beta",
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            2,
                                            "color",
                                            "Failed",
                                            [
                                                "str",
                                                "red"
                                            ],
                                            [
                                                "str",
                                                "blue"
                                            ]
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.089619+00:00",
                                    "exclude_keys": null,
                                    "line_no": 542
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "Dict match: Custom comparators",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.091710+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            0,
                                            "",
                                            "Passed",
                                            [
                                                "int",
                                                "1"
                                            ],
                                            [
                                                "int",
                                                "1"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            "Passed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            "Passed",
                                            [
                                                "int",
                                                "3"
                                            ],
                                            [
                                                "func",
                                                "<lambda>"
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            "color",
                                            "Passed",
                                            [
                                                "str",
                                                "blue"
                                            ],
                                            [
                                                "func",
                                                "VAL in ['blue', 'red', 'yellow']"
                                            ]
                                        ],
                                        [
                                            0,
                                            "baz",
                                            "Passed",
                                            [
                                                "str",
                                                "hello world"
                                            ],
                                            [
                                                "REGEX",
                                                "\\w+ world"
                                            ]
                                        ]
                                    ],
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:59.091718+00:00",
                                    "exclude_keys": null,
                                    "line_no": 560
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "default assertion passes because the values are numerically equal",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.093424+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Passed",
                                            [
                                                "int",
                                                "1"
                                            ],
                                            [
                                                "float",
                                                1.0
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            "Passed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "float",
                                                2.0
                                            ]
                                        ],
                                        [
                                            0,
                                            "baz",
                                            "Passed",
                                            [
                                                "int",
                                                "3"
                                            ],
                                            [
                                                "float",
                                                3.0
                                            ]
                                        ]
                                    ],
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:59.093432+00:00",
                                    "exclude_keys": null,
                                    "line_no": 572
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "when we check types the assertion will fail",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.094973+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Failed",
                                            [
                                                "int",
                                                "1"
                                            ],
                                            [
                                                "float",
                                                1.0
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            "Failed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "float",
                                                2.0
                                            ]
                                        ],
                                        [
                                            0,
                                            "baz",
                                            "Failed",
                                            [
                                                "int",
                                                "3"
                                            ],
                                            [
                                                "float",
                                                3.0
                                            ]
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.094981+00:00",
                                    "exclude_keys": null,
                                    "line_no": 578
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "use a custom comparison function to check within a tolerance",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.096547+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "foo",
                                            "Passed",
                                            [
                                                "float",
                                                1.02
                                            ],
                                            [
                                                "float",
                                                0.98
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            "Passed",
                                            [
                                                "float",
                                                2.28
                                            ],
                                            [
                                                "float",
                                                2.33
                                            ]
                                        ],
                                        [
                                            0,
                                            "baz",
                                            "Passed",
                                            [
                                                "float",
                                                3.5
                                            ],
                                            [
                                                "float",
                                                3.46
                                            ]
                                        ]
                                    ],
                                    "passed": true,
                                    "machine_time": "2020-01-10T11:06:59.096554+00:00",
                                    "exclude_keys": null,
                                    "line_no": 587
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "only report the failing comparison",
                                    "meta_type": "assertion",
                                    "type": "DictMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.098102+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            "bad_key",
                                            "Failed",
                                            [
                                                "str",
                                                "actual"
                                            ],
                                            [
                                                "str",
                                                "expected"
                                            ]
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.098109+00:00",
                                    "exclude_keys": null,
                                    "line_no": 601
                                },
                                {
                                    "absent_keys_diff": [
                                        "bar"
                                    ],
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "has_keys_diff": [
                                        "alpha"
                                    ],
                                    "type": "DictCheck",
                                    "utc_time": "2020-01-10T03:06:59.099751+00:00",
                                    "passed": false,
                                    "absent_keys": [
                                        "bar",
                                        "beta"
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.099760+00:00",
                                    "line_no": 611,
                                    "has_keys": [
                                        "foo",
                                        "alpha"
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "entry",
                                    "type": "DictLog",
                                    "utc_time": "2020-01-10T03:06:59.101282+00:00",
                                    "flattened_dict": [
                                        [
                                            0,
                                            "foo",
                                            ""
                                        ],
                                        [
                                            0,
                                            "",
                                            [
                                                "int",
                                                "1"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            [
                                                "int",
                                                "3"
                                            ]
                                        ],
                                        [
                                            0,
                                            "bar",
                                            ""
                                        ],
                                        [
                                            1,
                                            "color",
                                            [
                                                "str",
                                                "blue"
                                            ]
                                        ],
                                        [
                                            0,
                                            "baz",
                                            [
                                                "str",
                                                "hello world"
                                            ]
                                        ]
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.101290+00:00",
                                    "line_no": 620
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 0,
                                "failed": 1,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "826ee3d4-0dea-412b-9652-86f5847706d9",
                            "status": "failed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:59.116938+00:00",
                                    "start": "2020-01-10T03:06:59.111312+00:00"
                                }
                            },
                            "hash": 3253704292606433761,
                            "runtime_status": "finished",
                            "name": "test_fix_namespace",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "type": "FixMatch",
                                    "include_keys": null,
                                    "utc_time": "2020-01-10T03:06:59.111446+00:00",
                                    "actual_description": null,
                                    "expected_description": null,
                                    "comparison": [
                                        [
                                            0,
                                            36,
                                            "Passed",
                                            [
                                                "int",
                                                "6"
                                            ],
                                            [
                                                "int",
                                                "6"
                                            ]
                                        ],
                                        [
                                            0,
                                            22,
                                            "Passed",
                                            [
                                                "int",
                                                "5"
                                            ],
                                            [
                                                "int",
                                                "5"
                                            ]
                                        ],
                                        [
                                            0,
                                            55,
                                            "Passed",
                                            [
                                                "int",
                                                "2"
                                            ],
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ],
                                        [
                                            0,
                                            38,
                                            "Passed",
                                            [
                                                "int",
                                                "5"
                                            ],
                                            [
                                                "func",
                                                "VAL >= 4"
                                            ]
                                        ],
                                        [
                                            0,
                                            555,
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            0,
                                            "",
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            600,
                                            "Passed",
                                            [
                                                "str",
                                                "A"
                                            ],
                                            [
                                                "str",
                                                "A"
                                            ]
                                        ],
                                        [
                                            1,
                                            601,
                                            "Failed",
                                            [
                                                "str",
                                                "A"
                                            ],
                                            [
                                                "str",
                                                "B"
                                            ]
                                        ],
                                        [
                                            1,
                                            683,
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            2,
                                            688,
                                            "Passed",
                                            [
                                                "str",
                                                "a"
                                            ],
                                            [
                                                "str",
                                                "a"
                                            ]
                                        ],
                                        [
                                            2,
                                            689,
                                            "Passed",
                                            [
                                                "str",
                                                "a"
                                            ],
                                            [
                                                "REGEX",
                                                "[a-z]"
                                            ]
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            2,
                                            688,
                                            "Passed",
                                            [
                                                "str",
                                                "b"
                                            ],
                                            [
                                                "str",
                                                "b"
                                            ]
                                        ],
                                        [
                                            2,
                                            689,
                                            "Passed",
                                            [
                                                "str",
                                                "b"
                                            ],
                                            [
                                                "str",
                                                "b"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            "Failed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            600,
                                            "Failed",
                                            [
                                                "str",
                                                "B"
                                            ],
                                            [
                                                "str",
                                                "C"
                                            ]
                                        ],
                                        [
                                            1,
                                            601,
                                            "Passed",
                                            [
                                                "str",
                                                "B"
                                            ],
                                            [
                                                "str",
                                                "B"
                                            ]
                                        ],
                                        [
                                            1,
                                            683,
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            2,
                                            688,
                                            "Passed",
                                            [
                                                "str",
                                                "c"
                                            ],
                                            [
                                                "str",
                                                "c"
                                            ]
                                        ],
                                        [
                                            2,
                                            689,
                                            "Passed",
                                            [
                                                "str",
                                                "c"
                                            ],
                                            [
                                                "func",
                                                "VAL in ('c', 'd')"
                                            ]
                                        ],
                                        [
                                            1,
                                            "",
                                            "Passed",
                                            "",
                                            ""
                                        ],
                                        [
                                            2,
                                            688,
                                            "Passed",
                                            [
                                                "str",
                                                "d"
                                            ],
                                            [
                                                "str",
                                                "d"
                                            ]
                                        ],
                                        [
                                            2,
                                            689,
                                            "Passed",
                                            [
                                                "str",
                                                "d"
                                            ],
                                            [
                                                "str",
                                                "d"
                                            ]
                                        ]
                                    ],
                                    "passed": false,
                                    "machine_time": "2020-01-10T11:06:59.111452+00:00",
                                    "exclude_keys": null,
                                    "line_no": 708
                                },
                                {
                                    "absent_keys_diff": [
                                        555
                                    ],
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "assertion",
                                    "has_keys_diff": [
                                        26,
                                        11
                                    ],
                                    "type": "FixCheck",
                                    "utc_time": "2020-01-10T03:06:59.113689+00:00",
                                    "passed": false,
                                    "absent_keys": [
                                        444,
                                        555
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.113697+00:00",
                                    "line_no": 716,
                                    "has_keys": [
                                        26,
                                        22,
                                        11
                                    ]
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": null,
                                    "meta_type": "entry",
                                    "type": "FixLog",
                                    "utc_time": "2020-01-10T03:06:59.115483+00:00",
                                    "flattened_dict": [
                                        [
                                            0,
                                            36,
                                            [
                                                "int",
                                                "6"
                                            ]
                                        ],
                                        [
                                            0,
                                            22,
                                            [
                                                "int",
                                                "5"
                                            ]
                                        ],
                                        [
                                            0,
                                            55,
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ],
                                        [
                                            0,
                                            38,
                                            [
                                                "int",
                                                "5"
                                            ]
                                        ],
                                        [
                                            0,
                                            555,
                                            ""
                                        ],
                                        [
                                            0,
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            556,
                                            [
                                                "str",
                                                "USD"
                                            ]
                                        ],
                                        [
                                            1,
                                            624,
                                            [
                                                "int",
                                                "1"
                                            ]
                                        ],
                                        [
                                            0,
                                            "",
                                            ""
                                        ],
                                        [
                                            1,
                                            556,
                                            [
                                                "str",
                                                "EUR"
                                            ]
                                        ],
                                        [
                                            1,
                                            624,
                                            [
                                                "int",
                                                "2"
                                            ]
                                        ]
                                    ],
                                    "machine_time": "2020-01-10T11:06:59.115490+00:00",
                                    "line_no": 729
                                }
                            ]
                        },
                        {
                            "category": "testcase",
                            "logs": [],
                            "description": null,
                            "suite_related": false,
                            "counter": {
                                "passed": 1,
                                "failed": 0,
                                "total": 1
                            },
                            "status_reason": null,
                            "type": "TestCaseReport",
                            "uid": "52a8a7d9-80e6-4f7f-8eef-065bb25d38f8",
                            "status": "passed",
                            "parent_uids": [
                                "Assertions Example",
                                "Assertions Test",
                                "SampleSuite"
                            ],
                            "timer": {
                                "run": {
                                    "end": "2020-01-10T03:06:59.129247+00:00",
                                    "start": "2020-01-10T03:06:59.123570+00:00"
                                }
                            },
                            "hash": -5041530229790182508,
                            "runtime_status": "finished",
                            "name": "test_xml_namespace",
                            "status_override": null,
                            "tags": {},
                            "entries": [
                                {
                                    "category": "DEFAULT",
                                    "description": "Simple XML check for existence of xpath.",
                                    "meta_type": "assertion",
                                    "type": "XMLCheck",
                                    "utc_time": "2020-01-10T03:06:59.123813+00:00",
                                    "namespaces": null,
                                    "data": [],
                                    "passed": true,
                                    "xml": "<Root>\n                <Test>Foo</Test>\n            </Root>\n",
                                    "machine_time": "2020-01-10T11:06:59.123821+00:00",
                                    "tags": null,
                                    "line_no": 751,
                                    "message": "xpath: `/Root/Test` exists in the XML.",
                                    "xpath": "/Root/Test"
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "XML check for tags in the given xpath.",
                                    "meta_type": "assertion",
                                    "type": "XMLCheck",
                                    "utc_time": "2020-01-10T03:06:59.125438+00:00",
                                    "namespaces": null,
                                    "data": [
                                        [
                                            "Value1",
                                            null,
                                            null,
                                            null
                                        ],
                                        [
                                            "Value2",
                                            null,
                                            null,
                                            null
                                        ]
                                    ],
                                    "passed": true,
                                    "xml": "<Root>\n                <Test>Value1</Test>\n                <Test>Value2</Test>\n            </Root>\n",
                                    "machine_time": "2020-01-10T11:06:59.125447+00:00",
                                    "tags": [
                                        "Value1",
                                        "Value2"
                                    ],
                                    "line_no": 765,
                                    "message": null,
                                    "xpath": "/Root/Test"
                                },
                                {
                                    "category": "DEFAULT",
                                    "description": "XML check with namespace matching.",
                                    "meta_type": "assertion",
                                    "type": "XMLCheck",
                                    "utc_time": "2020-01-10T03:06:59.127250+00:00",
                                    "namespaces": {
                                        "a": "http://testplan"
                                    },
                                    "data": [
                                        [
                                            "Hello world!",
                                            null,
                                            null,
                                            "REGEX(Hello*)"
                                        ]
                                    ],
                                    "passed": true,
                                    "xml": "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\">\n                <SOAP-ENV:Header/>\n                <SOAP-ENV:Body>\n                    <ns0:message xmlns:ns0=\"http://testplan\">Hello world!</ns0:message>\n                </SOAP-ENV:Body>\n            </SOAP-ENV:Envelope>\n",
                                    "machine_time": "2020-01-10T11:06:59.127259+00:00",
                                    "tags": [
                                        "re.compile('Hello*')"
                                    ],
                                    "line_no": 784,
                                    "message": null,
                                    "xpath": "//*/a:message"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

const taggedReport = {
    "meta": {},
    "tags_index": {
        "color": ["yellow", "blue", "red", "white"],
        "simple": ["server", "client"],
    },
    "information": [
        ["user", "KN"],
        [
            "command_line_string",
            "C:/testplan/examples/Multitest/Tagging and Filtering/Basic Filters/test_plan_command_line.py --json a.json",
        ],
        ["python_version", "3.8.2"],
    ],
    "counter": {"passed": 8, "failed": 0, "total": 8},
    "timer": {
        "run": {
            "end": "2020-09-25T14:37:19.326452+00:00",
            "start": "2020-09-25T14:37:19.013195+00:00",
        }
    },
    "status": "passed",
    "logs": [],
    "uid": "88b2fed0-7c83-4e8c-9ae3-16ea156cf072",
    "timeout": 14400,
    "category": "testplan",
    "name": "Tagging_Filtering_Command_line",
    "entries": [
        {
            "hash": 1590703602743315515,
            "timer": {
                "run": {
                    "end": "2020-09-25T14:37:19.088037+00:00",
                    "start": "2020-09-25T14:37:19.083079+00:00",
                }
            },
            "logs": [],
            "status_reason": null,
            "name": "Primary",
            "entries": [
                {
                    "hash": -3721249419309028807,
                    "timer": {
                        "run": {
                            "end": "2020-09-25T14:37:19.085069+00:00",
                            "start": "2020-09-25T14:37:19.083079+00:00",
                        }
                    },
                    "logs": [],
                    "status_reason": null,
                    "name": "Alpha",
                    "entries": [
                        {
                            "suite_related": false,
                            "hash": -360398798333668410,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.084048+00:00",
                                    "start": "2020-09-25T14:37:19.084048+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "b0ac9bff-a172-45ea-a9a9-8380dcd60957",
                            "category": "testcase",
                            "name": "test_1",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Primary",
                                "Alpha",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                        {
                            "suite_related": false,
                            "hash": 2879499515688307282,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.084048+00:00",
                                    "start": "2020-09-25T14:37:19.084048+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "a4f1c333-2663-4acb-ab07-1ab2410a8636",
                            "category": "testcase",
                            "name": "test_2",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Primary",
                                "Alpha",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                    ],
                    "status_override": null,
                    "tags": {},
                    "env_status": null,
                    "status": "passed",
                    "category": "testsuite",
                    "runtime_status": "finished",
                    "counter": {"passed": 2, "failed": 0, "total": 2},
                    "extra_attributes": {},
                    "part": null,
                    "type": "TestGroupReport",
                    "description": null,
                    "fix_spec_path": null,
                    "uid": "1f6d810c-122b-45a4-b264-f5f10e51dc11",
                    "parent_uids": [
                        "Tagging_Filtering_Command_line",
                        "Primary",
                    ],
                },
                {
                    "hash": 7885919957307273304,
                    "timer": {
                        "run": {
                            "end": "2020-09-25T14:37:19.087040+00:00",
                            "start": "2020-09-25T14:37:19.085069+00:00",
                        }
                    },
                    "logs": [],
                    "status_reason": null,
                    "name": "Beta",
                    "entries": [
                        {
                            "suite_related": false,
                            "hash": -3272901787197531342,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"simple": ["server"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.085069+00:00",
                                    "start": "2020-09-25T14:37:19.085069+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "948d7e14-ff50-4fd1-adf7-b780d90489df",
                            "category": "testcase",
                            "name": "test_1",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Primary",
                                "Beta",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                        {
                            "suite_related": false,
                            "hash": 3686869030648441200,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"color": ["blue"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.086043+00:00",
                                    "start": "2020-09-25T14:37:19.086043+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "9a78c628-ea42-40cd-92dd-44aceacba502",
                            "category": "testcase",
                            "name": "test_2",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Primary",
                                "Beta",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                        {
                            "suite_related": false,
                            "hash": 5735591787756764475,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"simple": ["server"], "color": ["blue"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.086043+00:00",
                                    "start": "2020-09-25T14:37:19.086043+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "ce66a1a3-bf97-4886-9f7f-d86d1c65525a",
                            "category": "testcase",
                            "name": "test_3",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Primary",
                                "Beta",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                    ],
                    "status_override": null,
                    "tags": {},
                    "env_status": null,
                    "status": "passed",
                    "category": "testsuite",
                    "runtime_status": "finished",
                    "counter": {"passed": 3, "failed": 0, "total": 3},
                    "extra_attributes": {},
                    "part": null,
                    "type": "TestGroupReport",
                    "description": null,
                    "fix_spec_path": null,
                    "uid": "cdd13895-ad6c-41da-ac91-141c47e0fefa",
                    "parent_uids": [
                        "Tagging_Filtering_Command_line",
                        "Primary",
                    ],
                },
            ],
            "status_override": null,
            "tags": {"color": ["white"]},
            "env_status": "STOPPED",
            "status": "passed",
            "category": "multitest",
            "runtime_status": "finished",
            "counter": {"passed": 5, "failed": 0, "total": 5},
            "extra_attributes": {},
            "part": null,
            "type": "TestGroupReport",
            "description": null,
            "fix_spec_path": null,
            "uid": "b8feb53b-bc66-4b65-9a22-b9575ad6aaa5",
            "parent_uids": ["Tagging_Filtering_Command_line"],
        },
        {
            "hash": 2379047133263321405,
            "timer": {
                "run": {
                    "end": "2020-09-25T14:37:19.151866+00:00",
                    "start": "2020-09-25T14:37:19.149892+00:00",
                }
            },
            "logs": [],
            "status_reason": null,
            "name": "Secondary",
            "entries": [
                {
                    "hash": 8336773102611710315,
                    "timer": {
                        "run": {
                            "end": "2020-09-25T14:37:19.150868+00:00",
                            "start": "2020-09-25T14:37:19.149892+00:00",
                        }
                    },
                    "logs": [],
                    "status_reason": null,
                    "name": "Gamma",
                    "entries": [
                        {
                            "suite_related": false,
                            "hash": -4558038827978282586,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"color": ["red"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.149892+00:00",
                                    "start": "2020-09-25T14:37:19.149892+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "24c4c29d-ae81-4bdd-8dec-d1fd2996d90f",
                            "category": "testcase",
                            "name": "test_1",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Secondary",
                                "Gamma",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                        {
                            "suite_related": false,
                            "hash": 1452126978772489752,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"color": ["blue", "red"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.150868+00:00",
                                    "start": "2020-09-25T14:37:19.150868+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "a75e3ac5-a232-4a3e-a0e2-53ae74c30f5c",
                            "category": "testcase",
                            "name": "test_2",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Secondary",
                                "Gamma",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                        {
                            "suite_related": false,
                            "hash": 8615470789101300681,
                            "counter": {"passed": 1, "failed": 0, "total": 1},
                            "type": "TestCaseReport",
                            "description": null,
                            "tags": {"color": ["yellow"]},
                            "timer": {
                                "run": {
                                    "end": "2020-09-25T14:37:19.150868+00:00",
                                    "start": "2020-09-25T14:37:19.150868+00:00",
                                }
                            },
                            "status": "passed",
                            "logs": [],
                            "status_reason": null,
                            "uid": "2be4ed87-c617-418a-bdfd-554073a12836",
                            "category": "testcase",
                            "name": "test_3",
                            "entries": [],
                            "parent_uids": [
                                "Tagging_Filtering_Command_line",
                                "Secondary",
                                "Gamma",
                            ],
                            "runtime_status": "finished",
                            "status_override": null,
                        },
                    ],
                    "status_override": null,
                    "tags": {"simple": ["server", "client"]},
                    "env_status": null,
                    "status": "passed",
                    "category": "testsuite",
                    "runtime_status": "finished",
                    "counter": {"passed": 3, "failed": 0, "total": 3},
                    "extra_attributes": {},
                    "part": null,
                    "type": "TestGroupReport",
                    "description": null,
                    "fix_spec_path": null,
                    "uid": "05a137d1-b72b-4cec-b132-8302cce7b02d",
                    "parent_uids": [
                        "Tagging_Filtering_Command_line",
                        "Secondary",
                    ],
                }
            ],
            "status_override": null,
            "tags": {},
            "env_status": "STOPPED",
            "status": "passed",
            "category": "multitest",
            "runtime_status": "finished",
            "counter": {"passed": 3, "failed": 0, "total": 3},
            "extra_attributes": {},
            "part": null,
            "type": "TestGroupReport",
            "description": null,
            "fix_spec_path": null,
            "uid": "032d6dd5-4be1-45cb-b914-43022acae295",
            "parent_uids": ["Tagging_Filtering_Command_line"],
        },
    ],
    "attachments": {},
    "runtime_status": "finished",
    "status_override": null,
    "version": 1,
}


export {
  TESTPLAN_REPORT,
  fakeReportAssertions,
  taggedReport
}
