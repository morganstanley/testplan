/**
 * Sample Testplan reports to be used in development & testing.
 */
const TESTPLAN_REPORT = {
  "name": "Sample Testplan",
  "status": "failed",
  "uid": "520a92e4-325e-4077-93e6-55d7091a3f83",
  "tags_index": {},
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
          "category": "suite",
          "name": "AlphaSuite",
          "status_override": null,
          "description": null,
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
              "status": "passed",
              "status_override": null,
              "description": null,
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
          "category": "suite",
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
          "category": "suite",
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
"status": "failed", "uid": "94a616f8-4400-4ca4-b213-32664701ca8a", "tags_index": {}, "timer": {
    "run": {
        "start": "2019-02-12T17:41:42.707149+00:00",
        "end": "2019-02-12T17:41:43.534854+00:00"
    }
}, "status_override": null, "meta": {}, "entries": [{
        "status": "failed",
        "category": "multitest",
        "name": "Assertions Test",
        "tags": {},
        "description": null,
        "timer": {
            "run": {
                "start": "2019-02-12T17:41:42.795281+00:00",
                "end": "2019-02-12T17:41:43.334400+00:00"
            }
        },
        "status_override": null,
        "part": null,
        "entries": [{
                "status": "failed",
                "category": "suite",
                "name": "SampleSuite",
                "tags": {},
                "description": null,
                "timer": {
                    "run": {
                        "start": "2019-02-12T17:41:42.795390+00:00",
                        "end": "2019-02-12T17:41:43.332348+00:00"
                    }
                },
                "status_override": null,
                "part": null,
                "entries": [{
                        "status": "failed",
                        "name": "test_basic_assertions",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:42.795489+00:00",
                                "end": "2019-02-12T17:41:43.060889+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:42.795536+00:00",
                                "description": null,
                                "line_no": 25,
                                "label": "==",
                                "second": "foo",
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Equal",
                                "utc_time": "2019-02-12T17:41:42.795530+00:00",
                                "first": "foo"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.019771+00:00",
                                "description": "Description for failing equality",
                                "line_no": 28,
                                "label": "==",
                                "second": 2,
                                "meta_type": "assertion",
                                "passed": false,
                                "type": "Equal",
                                "utc_time": "2019-02-12T17:41:43.019761+00:00",
                                "first": 1
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.021937+00:00",
                                "description": null,
                                "line_no": 30,
                                "label": "!=",
                                "second": "bar",
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "NotEqual",
                                "utc_time": "2019-02-12T17:41:43.021930+00:00",
                                "first": "foo"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.023470+00:00",
                                "description": null,
                                "line_no": 31,
                                "label": ">",
                                "second": 2,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Greater",
                                "utc_time": "2019-02-12T17:41:43.023464+00:00",
                                "first": 5
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.025466+00:00",
                                "description": null,
                                "line_no": 32,
                                "label": ">=",
                                "second": 2,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "GreaterEqual",
                                "utc_time": "2019-02-12T17:41:43.025459+00:00",
                                "first": 2
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.027089+00:00",
                                "description": null,
                                "line_no": 33,
                                "label": ">=",
                                "second": 1,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "GreaterEqual",
                                "utc_time": "2019-02-12T17:41:43.027083+00:00",
                                "first": 2
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.028544+00:00",
                                "description": null,
                                "line_no": 34,
                                "label": "<",
                                "second": 20,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Less",
                                "utc_time": "2019-02-12T17:41:43.028537+00:00",
                                "first": 10
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.029897+00:00",
                                "description": null,
                                "line_no": 35,
                                "label": "<=",
                                "second": 10,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "LessEqual",
                                "utc_time": "2019-02-12T17:41:43.029890+00:00",
                                "first": 10
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.031373+00:00",
                                "description": null,
                                "line_no": 36,
                                "label": "<=",
                                "second": 30,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "LessEqual",
                                "utc_time": "2019-02-12T17:41:43.031367+00:00",
                                "first": 10
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.033139+00:00",
                                "description": null,
                                "line_no": 41,
                                "label": "==",
                                "second": 15,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Equal",
                                "utc_time": "2019-02-12T17:41:43.033133+00:00",
                                "first": 15
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.034645+00:00",
                                "description": null,
                                "line_no": 42,
                                "label": "!=",
                                "second": 20,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "NotEqual",
                                "utc_time": "2019-02-12T17:41:43.034639+00:00",
                                "first": 10
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.036234+00:00",
                                "description": null,
                                "line_no": 43,
                                "label": "<",
                                "second": 3,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Less",
                                "utc_time": "2019-02-12T17:41:43.036228+00:00",
                                "first": 2
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.037659+00:00",
                                "description": null,
                                "line_no": 44,
                                "label": ">",
                                "second": 2,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Greater",
                                "utc_time": "2019-02-12T17:41:43.037653+00:00",
                                "first": 3
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.039108+00:00",
                                "description": null,
                                "line_no": 45,
                                "label": "<=",
                                "second": 15,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "LessEqual",
                                "utc_time": "2019-02-12T17:41:43.039101+00:00",
                                "first": 10
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.040526+00:00",
                                "description": null,
                                "line_no": 46,
                                "label": ">=",
                                "second": 10,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "GreaterEqual",
                                "utc_time": "2019-02-12T17:41:43.040520+00:00",
                                "first": 15
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.042097+00:00",
                                "description": null,
                                "abs_tol": 0.0,
                                "line_no": 50,
                                "rel_tol": 0.1,
                                "label": "~=",
                                "second": 95,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "IsClose",
                                "utc_time": "2019-02-12T17:41:43.042090+00:00",
                                "first": 100
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.043757+00:00",
                                "description": null,
                                "abs_tol": 0.0,
                                "line_no": 51,
                                "rel_tol": 0.01,
                                "label": "~=",
                                "second": 95,
                                "meta_type": "assertion",
                                "passed": false,
                                "type": "IsClose",
                                "utc_time": "2019-02-12T17:41:43.043751+00:00",
                                "first": 100
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "message": "This is a log message, it will be displayed along with other assertion details.",
                                "type": "Log",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.046710+00:00",
                                "description": "Boolean Truthiness check",
                                "expr": true,
                                "line_no": 61,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "IsTrue",
                                "utc_time": "2019-02-12T17:41:43.046704+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.048126+00:00",
                                "description": "Boolean Falseness check",
                                "expr": false,
                                "line_no": 62,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "IsFalse",
                                "utc_time": "2019-02-12T17:41:43.048120+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.049460+00:00",
                                "description": "This is an explicit failure.",
                                "line_no": 64,
                                "meta_type": "assertion",
                                "passed": false,
                                "type": "Fail",
                                "utc_time": "2019-02-12T17:41:43.049454+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.050888+00:00",
                                "container": "foobar",
                                "description": "Passing membership",
                                "line_no": 67,
                                "member": "foo",
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Contain",
                                "utc_time": "2019-02-12T17:41:43.050882+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.052594+00:00",
                                "container": "{'a': 1, 'b': 2}",
                                "description": "Failing membership",
                                "line_no": 71,
                                "member": 10,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "NotContain",
                                "utc_time": "2019-02-12T17:41:43.052579+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.053943+00:00",
                                "actual": [1, 2, 3, 4, 5, 6, 7, 8],
                                "description": "Comparison of slices",
                                "data": [["slice(2, 4, None)", [2, 3], [], [3, 4], [3, 4]], ["slice(6, 8, None)", [6, 7], [], [7, 8], [7, 8]]],
                                "line_no": 79,
                                "included_indices": [],
                                "meta_type": "assertion",
                                "passed": true,
                                "expected": ["a", "b", 3, 4, "c", "d", 7, 8],
                                "type": "EqualSlices",
                                "utc_time": "2019-02-12T17:41:43.053936+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.055991+00:00",
                                "actual": [1, 2, 3, 4, 5, 6, 7, 8],
                                "description": "Comparison of slices (exclusion)",
                                "data": [["slice(0, 2, None)", [2, 3, 4, 5, 6, 7], [4, 5, 6, 7], [3, 4, 5, 6, 7, 8], [3, 4, "c", "d", "e", "f"]], ["slice(4, 8, None)", [0, 1, 2, 3], [0, 1], [1, 2, 3, 4], ["a", "b", 3, 4]]],
                                "line_no": 91,
                                "included_indices": [2, 3],
                                "meta_type": "assertion",
                                "passed": true,
                                "expected": ["a", "b", 3, 4, "c", "d", "e", "f"],
                                "type": "EqualExcludeSlices",
                                "utc_time": "2019-02-12T17:41:43.055984+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.057544+00:00",
                                "ignore_space_change": false,
                                "description": null,
                                "unified": false,
                                "type": "LineDiff",
                                "line_no": 98,
                                "second": ["abc\n", "xyz\n", "\n"],
                                "meta_type": "assertion",
                                "context": false,
                                "ignore_whitespaces": false,
                                "delta": [],
                                "ignore_blank_lines": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.057524+00:00",
                                "first": ["abc\n", "xyz\n"]
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.059150+00:00",
                                "ignore_space_change": true,
                                "description": null,
                                "unified": 3,
                                "type": "LineDiff",
                                "line_no": 102,
                                "second": ["1\n", "1\n", "1\n", "abc \n", "xy\t\tz\n", "2\n", "2\n", "2\n"],
                                "meta_type": "assertion",
                                "context": false,
                                "ignore_whitespaces": false,
                                "delta": [],
                                "ignore_blank_lines": false,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.059145+00:00",
                                "first": ["1\r\n", "1\r\n", "1\r\n", "abc\r\n", "xy z\r\n", "2\r\n", "2\r\n", "2\r\n"]
                            },{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                          {x: 0, y: 8},
                                          {x: 1, y: 5},
                                          {x: 2, y: 4},
                                          {x: 3, y: 9},
                                          {x: 4, y: 1},
                                          {x: 5, y: 7},
                                          {x: 6, y: 6},
                                          {x: 7, y: 3},
                                          {x: 8, y: 2},
                                          {x: 9, y: 0}
                                        ],
                                "type": "Graph",
                                "graph_type": "Line",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             },{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                  {x: 'A', y: 10},
                                  {x: 'B', y: 5},
                                  {x: 'C', y: 15}
                                ],
                                "type": "Graph",
                                "graph_type": "Bar",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             }
                             ,{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                          {x: 0, y: 8},
                                          {x: 1, y: 5},
                                          {x: 2, y: 4},
                                          {x: 3, y: 9},
                                          {x: 4, y: 1},
                                          {x: 5, y: 7},
                                          {x: 6, y: 6},
                                          {x: 7, y: 3},
                                          {x: 8, y: 2},
                                          {x: 9, y: 0}
                                        ],
                                "type": "Graph",
                                "graph_type": "Hexbin",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             }
                              ,{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                          {x: 0, y: 8},
                                          {x: 1, y: 50},
                                          {x: 2, y: 4},
                                          {x: -10, y: 9},
                                          {x: 4, y: 1},
                                          {x: 5, y: 7},
                                          {x: 6, y: -3},
                                          {x: 7, y: 3},
                                          {x: 100, y: 2},
                                          {x: 9, y: 0}
                                        ],
                                "type": "Graph",
                                "graph_type": "Contour",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             }
                             ,{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                          {x: 1, y: 10, xVariance: 4, yVariance: 4},
                                          {x: 1.7, y: 12, xVariance: 2, yVariance: 2},
                                          {x: 2, y: 5, xVariance: 3, yVariance: 3},
                                          {x: 3, y: 15, xVariance: 1, yVariance: 2},
                                          {x: 2.5, y: 7, xVariance: 4, yVariance: 4}
                                        ],
                                "type": "Graph",
                                "graph_type": "Whisker",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             },{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.045339+00:00",
                                "description": null,
                                "line_no": 56,
                                "meta_type": "entry",
                                "data": [
                                        {angle: 1, color: '#89DAC1', name: 'green', opacity: 0.2},
                                        {angle: 2, color: '#F6D18A', name: 'yellow'},
                                        {angle: 5, color: '#1E96BE', name: 'cyan'},
                                        {angle: 3, color: '#DA70BF', name: 'magenta'},
                                        {angle: 5, color: '#F6D18A', name: 'yellow again'}
                                      ],
                                "type": "DiscreteChart",
                                "graph_type": "Pie",
                                "utc_time": "2019-02-12T17:41:43.045333+00:00"
                             }

                        ],
                        "uid": "22758cc5-8a89-472b-bf67-b64dbc2c0b40",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "passed",
                        "name": "test_raised_exceptions",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.112235+00:00",
                                "end": "2019-02-12T17:41:43.122266+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.112284+00:00",
                                "description": null,
                                "exception_match": true,
                                "pattern": null,
                                "line_no": 112,
                                "expected_exceptions": ["KeyError"],
                                "meta_type": "assertion",
                                "raised_exception": ["<type 'exceptions.KeyError'>", "'bar'"],
                                "func": null,
                                "type": "ExceptionRaised",
                                "func_match": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.112279+00:00",
                                "pattern_match": true
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.113904+00:00",
                                "description": "Exception raised with custom pattern.",
                                "exception_match": true,
                                "pattern": "foobar",
                                "line_no": 121,
                                "expected_exceptions": ["ValueError"],
                                "meta_type": "assertion",
                                "raised_exception": ["<type 'exceptions.ValueError'>", "abc foobar xyz"],
                                "func": null,
                                "type": "ExceptionRaised",
                                "func_match": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.113897+00:00",
                                "pattern_match": true
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.115702+00:00",
                                "description": "Exception raised with custom func.",
                                "exception_match": true,
                                "pattern": null,
                                "line_no": 139,
                                "expected_exceptions": ["MyException"],
                                "meta_type": "assertion",
                                "raised_exception": ["<class '__main__.MyException'>", ""],
                                "func": "<function custom_func at 0x7f1636de7f50>",
                                "type": "ExceptionRaised",
                                "func_match": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.115690+00:00",
                                "pattern_match": true
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.117589+00:00",
                                "description": null,
                                "exception_match": false,
                                "pattern": null,
                                "line_no": 146,
                                "expected_exceptions": ["TypeError"],
                                "meta_type": "assertion",
                                "raised_exception": ["<type 'exceptions.KeyError'>", "'bar'"],
                                "func": null,
                                "type": "ExceptionNotRaised",
                                "func_match": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.117579+00:00",
                                "pattern_match": true
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.119128+00:00",
                                "description": "Exception not raised with custom pattern.",
                                "exception_match": true,
                                "pattern": "foobar",
                                "line_no": 157,
                                "expected_exceptions": ["ValueError"],
                                "meta_type": "assertion",
                                "raised_exception": ["<type 'exceptions.ValueError'>", "abc"],
                                "func": null,
                                "type": "ExceptionNotRaised",
                                "func_match": true,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.119120+00:00",
                                "pattern_match": null
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.120596+00:00",
                                "description": "Exception not raised with custom func.",
                                "exception_match": true,
                                "pattern": null,
                                "line_no": 165,
                                "expected_exceptions": ["MyException"],
                                "meta_type": "assertion",
                                "raised_exception": ["<class '__main__.MyException'>", ""],
                                "func": "<function custom_func at 0x7f1636de7f50>",
                                "type": "ExceptionNotRaised",
                                "func_match": false,
                                "passed": true,
                                "utc_time": "2019-02-12T17:41:43.120588+00:00",
                                "pattern_match": true
                            }
                        ],
                        "uid": "ddb9ea4b-1d95-4948-b427-9abafd315b8d",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "failed",
                        "name": "test_assertion_group",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.130541+00:00",
                                "end": "2019-02-12T17:41:43.138126+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.130589+00:00",
                                "description": "Equality assertion outside the group",
                                "line_no": 173,
                                "label": "==",
                                "second": 1,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Equal",
                                "utc_time": "2019-02-12T17:41:43.130585+00:00",
                                "first": 1
                            }, {
                                "meta_type": "assertion",
                                "type": "Group",
                                "description": "Custom group description",
                                "passed": false,
                                "entries": [{
                                        "category": "DEFAULT",
                                        "machine_time": "2019-02-12T17:41:43.132415+00:00",
                                        "description": "Assertion within a group",
                                        "line_no": 176,
                                        "label": "!=",
                                        "second": 3,
                                        "meta_type": "assertion",
                                        "passed": true,
                                        "type": "NotEqual",
                                        "utc_time": "2019-02-12T17:41:43.132399+00:00",
                                        "first": 2
                                    }, {
                                        "category": "DEFAULT",
                                        "machine_time": "2019-02-12T17:41:43.133860+00:00",
                                        "description": null,
                                        "line_no": 177,
                                        "label": ">",
                                        "second": 3,
                                        "meta_type": "assertion",
                                        "passed": true,
                                        "type": "Greater",
                                        "utc_time": "2019-02-12T17:41:43.133854+00:00",
                                        "first": 5
                                    }, {
                                        "meta_type": "assertion",
                                        "type": "Group",
                                        "description": "This is a sub group",
                                        "passed": false,
                                        "entries": [{
                                                "category": "DEFAULT",
                                                "machine_time": "2019-02-12T17:41:43.135357+00:00",
                                                "description": "Assertion within sub group",
                                                "line_no": 181,
                                                "label": "<",
                                                "second": 3,
                                                "meta_type": "assertion",
                                                "passed": false,
                                                "type": "Less",
                                                "utc_time": "2019-02-12T17:41:43.135351+00:00",
                                                "first": 6
                                            }
                                        ]
                                    }
                                ]
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.136700+00:00",
                                "description": "Final assertion outside all groups",
                                "line_no": 184,
                                "label": "==",
                                "second": "foo",
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "Equal",
                                "utc_time": "2019-02-12T17:41:43.136694+00:00",
                                "first": "foo"
                            }
                        ],
                        "uid": "38ba8dc7-52dd-4005-ba8d-05bbad231a49",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "failed",
                        "name": "test_regex_namespace",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.145240+00:00",
                                "end": "2019-02-12T17:41:43.162524+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.145337+00:00",
                                "description": "string pattern match",
                                "pattern": "foo",
                                "line_no": 196,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [[0, 3]],
                                "type": "RegexMatch",
                                "utc_time": "2019-02-12T17:41:43.145332+00:00",
                                "string": "foobar"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.146933+00:00",
                                "description": "SRE match",
                                "pattern": "foo",
                                "line_no": 201,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [[0, 3]],
                                "type": "RegexMatch",
                                "utc_time": "2019-02-12T17:41:43.146927+00:00",
                                "string": "foobar"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.148410+00:00",
                                "description": null,
                                "pattern": "first line.*second",
                                "line_no": 212,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [[0, 17]],
                                "type": "RegexMatch",
                                "utc_time": "2019-02-12T17:41:43.148404+00:00",
                                "string": "first line\nsecond line\nthird line"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.150042+00:00",
                                "description": null,
                                "pattern": "baz",
                                "line_no": 217,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [],
                                "type": "RegexMatchNotExists",
                                "utc_time": "2019-02-12T17:41:43.150037+00:00",
                                "string": "foobar"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.151596+00:00",
                                "description": null,
                                "pattern": "foobar",
                                "line_no": 222,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [],
                                "type": "RegexMatchNotExists",
                                "utc_time": "2019-02-12T17:41:43.151590+00:00",
                                "string": "first line\nsecond line\nthird line"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.153301+00:00",
                                "description": null,
                                "pattern": "second",
                                "line_no": 225,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [[11, 17]],
                                "type": "RegexSearch",
                                "utc_time": "2019-02-12T17:41:43.153294+00:00",
                                "string": "first line\nsecond line\nthird line"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.154688+00:00",
                                "description": "Passing search empty",
                                "pattern": "foobar",
                                "line_no": 230,
                                "meta_type": "assertion",
                                "passed": true,
                                "match_indexes": [],
                                "type": "RegexSearchNotExists",
                                "utc_time": "2019-02-12T17:41:43.154681+00:00",
                                "string": "first line\nsecond line\nthird line"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.155980+00:00",
                                "description": "Failing search_empty",
                                "pattern": "second",
                                "line_no": 233,
                                "meta_type": "assertion",
                                "passed": false,
                                "match_indexes": [[11, 17]],
                                "type": "RegexSearchNotExists",
                                "utc_time": "2019-02-12T17:41:43.155974+00:00",
                                "string": "first line\nsecond line\nthird line"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.157637+00:00",
                                "description": null,
                                "string": "foo foo foo bar bar foo bar",
                                "pattern": "foo",
                                "line_no": 243,
                                "condition_match": true,
                                "meta_type": "assertion",
                                "condition": "<lambda>",
                                "passed": true,
                                "type": "RegexFindIter",
                                "utc_time": "2019-02-12T17:41:43.157630+00:00",
                                "match_indexes": [[0, 3], [4, 7], [8, 11], [20, 23]]
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.159271+00:00",
                                "description": null,
                                "string": "foo foo foo bar bar foo bar",
                                "pattern": "foo",
                                "line_no": 250,
                                "condition_match": true,
                                "meta_type": "assertion",
                                "condition": "(VAL > 2 and VAL < 5)",
                                "passed": true,
                                "type": "RegexFindIter",
                                "utc_time": "2019-02-12T17:41:43.159265+00:00",
                                "match_indexes": [[0, 3], [4, 7], [8, 11], [20, 23]]
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.160987+00:00",
                                "description": null,
                                "string": "first line\nsecond line\nthird line",
                                "pattern": "\\w+ line$",
                                "line_no": 257,
                                "meta_type": "assertion",
                                "passed": true,
                                "type": "RegexMatchLine",
                                "utc_time": "2019-02-12T17:41:43.160981+00:00",
                                "match_indexes": [[0, 0, 10], [1, 0, 11], [2, 0, 10]]
                            }
                        ],
                        "uid": "bbc6f5aa-2f4d-4784-be1f-419aec688ba3",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "failed",
                        "name": "test_table_namespace",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.176339+00:00",
                                "end": "2019-02-12T17:41:43.266173+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.176922+00:00",
                                "description": "Table Match: list of list vs list of list",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 284,
                                "data": [[0, ["Bob", 32], {}, {}, {}
                                    ], [1, ["Susan", 24], {}, {}, {}
                                    ], [2, ["Rick", 67], {}, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.176916+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.179172+00:00",
                                "description": "Table Match: list of dict vs list of dict",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 289,
                                "data": [[0, [32, "Bob"], {}, {}, {}
                                    ], [1, [24, "Susan"], {}, {}, {}
                                    ], [2, [67, "Rick"], {}, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["age", "name"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.179166+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.181633+00:00",
                                "description": "Table Match: list of dict vs list of list",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 294,
                                "data": [[0, [32, "Bob"], {}, {}, {}
                                    ], [1, [24, "Susan"], {}, {}, {}
                                    ], [2, [67, "Rick"], {}, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["age", "name"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.181627+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.183720+00:00",
                                "description": "Table Diff: list of list vs list of list",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 299,
                                "data": [],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.183714+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.185375+00:00",
                                "description": "Table Diff: list of dict vs list of dict",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 304,
                                "data": [],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["age", "name"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.185368+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.187247+00:00",
                                "description": "Table Diff: list of dict vs list of list",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 309,
                                "data": [],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["age", "name"],
                                "passed": true,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.187239+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.189243+00:00",
                                "description": "Table Match: simple comparators",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 338,
                                "data": [[0, ["Bob", 32], {}, {}, {
                                            "age": "<lambda>",
                                            "name": "REGEX(\\w{3})"
                                        }
                                    ], [1, ["Susan", 24], {}, {}, {}
                                    ], [2, ["Rick", 67], {
                                            "name": "<lambda>"
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.189235+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.191430+00:00",
                                "description": "Table Diff: simple comparators",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 343,
                                "data": [[2, ["Rick", 67], {
                                            "name": "<lambda>"
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.191421+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.194193+00:00",
                                "description": "Table Match: readable comparators",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 361,
                                "data": [[0, ["Bob", 32], {}, {}, {
                                            "age": "(VAL > 30 and VAL < 40)",
                                            "name": "REGEX(\\w{3})"
                                        }
                                    ], [1, ["Susan", 24], {}, {}, {}
                                    ], [2, ["Rick", 67], {
                                            "name": "VAL in ['David', 'Helen', 'Pablo']"
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.194183+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.196663+00:00",
                                "description": "Table Diff: readable comparators",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 366,
                                "data": [[2, ["Rick", 67], {
                                            "name": "VAL in ['David', 'Helen', 'Pablo']"
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["name", "age"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.196657+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.198817+00:00",
                                "description": "Table Match: Trimmed columns",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 0,
                                "line_no": 383,
                                "data": [[0, [0, 0], {}, {}, {}
                                    ], [1, [2, 1], {}, {}, {}
                                    ], [2, [4, 2], {}, {}, {}
                                    ], [3, [6, 3], {}, {}, {}
                                    ], [4, [8, 4], {}, {}, {}
                                    ], [5, [10, 5], {}, {}, {}
                                    ], [6, [12, 6], {}, {}, {}
                                    ], [7, [14, 7], {}, {}, {}
                                    ], [8, [16, 8], {}, {}, {}
                                    ], [9, [18, 9], {}, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["column_2", "column_1"],
                                "passed": true,
                                "include_columns": ["column_1", "column_2"],
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.198811+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.202946+00:00",
                                "description": "Table Diff: Trimmed columns",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 0,
                                "line_no": 391,
                                "data": [],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["column_2", "column_1"],
                                "passed": true,
                                "include_columns": ["column_1", "column_2"],
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.202939+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.207724+00:00",
                                "description": "Table Match: Trimmed rows",
                                "exclude_columns": null,
                                "report_fails_only": false,
                                "fail_limit": 2,
                                "line_no": 428,
                                "data": [[0, [0, 4473], {}, {}, {}
                                    ], [1, [10, 3158], {}, {}, {}
                                    ], [2, [20, 1768], {}, {}, {}
                                    ], [3, [30, 4409], {}, {}, {}
                                    ], [4, [40, 3683], {}, {}, {}
                                    ], [5, [25, 1111], {
                                            "amount": 35
                                        }, {}, {}
                                    ], [6, [20, 2222], {
                                            "product_id": 1234
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["amount", "product_id"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableMatch",
                                "utc_time": "2019-02-12T17:41:43.207717+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.212960+00:00",
                                "description": "Table Diff: Trimmed rows",
                                "exclude_columns": null,
                                "report_fails_only": true,
                                "fail_limit": 2,
                                "line_no": 437,
                                "data": [[5, [25, 1111], {
                                            "amount": 35
                                        }, {}, {}
                                    ], [6, [20, 2222], {
                                            "product_id": 1234
                                        }, {}, {}
                                    ]],
                                "strict": false,
                                "meta_type": "assertion",
                                "columns": ["amount", "product_id"],
                                "passed": false,
                                "include_columns": null,
                                "message": null,
                                "type": "TableDiff",
                                "utc_time": "2019-02-12T17:41:43.212949+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.215324+00:00",
                                "description": null,
                                "column": "symbol",
                                "type": "ColumnContain",
                                "line_no": 454,
                                "report_fails_only": false,
                                "meta_type": "assertion",
                                "limit": null,
                                "passed": false,
                                "values": ["AAPL", "AMZN"],
                                "data": [[0, "AAPL", true], [1, "GOOG", false], [2, "FB", false], [3, "AMZN", true], [4, "MSFT", false]],
                                "utc_time": "2019-02-12T17:41:43.215318+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.236233+00:00",
                                "description": null,
                                "column": "symbol",
                                "type": "ColumnContain",
                                "line_no": 467,
                                "report_fails_only": true,
                                "meta_type": "assertion",
                                "limit": 20,
                                "passed": false,
                                "values": ["AAPL", "AMZN"],
                                "data": [[1, "GOOG", false], [2, "FB", false], [4, "MSFT", false], [6, "GOOG", false], [7, "FB", false], [9, "MSFT", false], [11, "GOOG", false], [12, "FB", false], [14, "MSFT", false], [16, "GOOG", false], [17, "FB", false], [19, "MSFT", false], [21, "GOOG", false], [22, "FB", false], [24, "MSFT", false], [26, "GOOG", false], [27, "FB", false], [29, "MSFT", false], [31, "GOOG", false], [32, "FB", false]],
                                "utc_time": "2019-02-12T17:41:43.236220+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.241786+00:00",
                                "description": "Table Log: list of dicts",
                                "line_no": 472,
                                "display_index": false,
                                "meta_type": "entry",
                                "columns": ["age", "name"],
                                "indices": [0, 1, 2],
                                "table": [{
                                        "age": 32,
                                        "name": "Bob"
                                    }, {
                                        "age": 24,
                                        "name": "Susan"
                                    }, {
                                        "age": 67,
                                        "name": "Rick"
                                    }
                                ],
                                "type": "TableLog",
                                "utc_time": "2019-02-12T17:41:43.241777+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.243735+00:00",
                                "description": "Table Log: list of lists",
                                "line_no": 473,
                                "display_index": false,
                                "meta_type": "entry",
                                "columns": ["name", "age"],
                                "indices": [0, 1, 2],
                                "table": [{
                                        "age": 32,
                                        "name": "Bob"
                                    }, {
                                        "age": 24,
                                        "name": "Susan"
                                    }, {
                                        "age": 67,
                                        "name": "Rick"
                                    }
                                ],
                                "type": "TableLog",
                                "utc_time": "2019-02-12T17:41:43.243729+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.246144+00:00",
                                "description": "Table Log: many rows",
                                "line_no": 479,
                                "display_index": false,
                                "meta_type": "entry",
                                "columns": ["symbol", "amount"],
                                "indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
                                "table": [{
                                        "symbol": "AAPL",
                                        "amount": 12
                                    }, {
                                        "symbol": "GOOG",
                                        "amount": 21
                                    }, {
                                        "symbol": "FB",
                                        "amount": 32
                                    }, {
                                        "symbol": "AMZN",
                                        "amount": 5
                                    }, {
                                        "symbol": "MSFT",
                                        "amount": 42
                                    }, {
                                        "symbol": "AAPL",
                                        "amount": 12
                                    }, {
                                        "symbol": "GOOG",
                                        "amount": 21
                                    }, {
                                        "symbol": "FB",
                                        "amount": 32
                                    }, {
                                        "symbol": "AMZN",
                                        "amount": 5
                                    }, {
                                        "symbol": "MSFT",
                                        "amount": 42
                                    }, {
                                        "symbol": "AAPL",
                                        "amount": 12
                                    }, {
                                        "symbol": "GOOG",
                                        "amount": 21
                                    }, {
                                        "symbol": "FB",
                                        "amount": 32
                                    }, {
                                        "symbol": "AMZN",
                                        "amount": 5
                                    }, {
                                        "symbol": "MSFT",
                                        "amount": 42
                                    }, {
                                        "symbol": "AAPL",
                                        "amount": 12
                                    }, {
                                        "symbol": "GOOG",
                                        "amount": 21
                                    }, {
                                        "symbol": "FB",
                                        "amount": 32
                                    }, {
                                        "symbol": "AMZN",
                                        "amount": 5
                                    }, {
                                        "symbol": "MSFT",
                                        "amount": 42
                                    }
                                ],
                                "type": "TableLog",
                                "utc_time": "2019-02-12T17:41:43.246138+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.252173+00:00",
                                "description": "Table Log: many columns",
                                "line_no": 490,
                                "display_index": false,
                                "meta_type": "entry",
                                "columns": ["col_0", "col_1", "col_2", "col_3", "col_4", "col_5", "col_6", "col_7", "col_8", "col_9", "col_10", "col_11", "col_12", "col_13", "col_14", "col_15", "col_16", "col_17", "col_18", "col_19"],
                                "indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                                "table": [{
                                        "col_18": "row 0 col 18",
                                        "col_19": "row 0 col 19",
                                        "col_14": "row 0 col 14",
                                        "col_15": "row 0 col 15",
                                        "col_16": "row 0 col 16",
                                        "col_17": "row 0 col 17",
                                        "col_10": "row 0 col 10",
                                        "col_11": "row 0 col 11",
                                        "col_12": "row 0 col 12",
                                        "col_13": "row 0 col 13",
                                        "col_8": "row 0 col 8",
                                        "col_9": "row 0 col 9",
                                        "col_2": "row 0 col 2",
                                        "col_3": "row 0 col 3",
                                        "col_0": "row 0 col 0",
                                        "col_1": "row 0 col 1",
                                        "col_6": "row 0 col 6",
                                        "col_7": "row 0 col 7",
                                        "col_4": "row 0 col 4",
                                        "col_5": "row 0 col 5"
                                    }, {
                                        "col_18": "row 1 col 18",
                                        "col_19": "row 1 col 19",
                                        "col_14": "row 1 col 14",
                                        "col_15": "row 1 col 15",
                                        "col_16": "row 1 col 16",
                                        "col_17": "row 1 col 17",
                                        "col_10": "row 1 col 10",
                                        "col_11": "row 1 col 11",
                                        "col_12": "row 1 col 12",
                                        "col_13": "row 1 col 13",
                                        "col_8": "row 1 col 8",
                                        "col_9": "row 1 col 9",
                                        "col_2": "row 1 col 2",
                                        "col_3": "row 1 col 3",
                                        "col_0": "row 1 col 0",
                                        "col_1": "row 1 col 1",
                                        "col_6": "row 1 col 6",
                                        "col_7": "row 1 col 7",
                                        "col_4": "row 1 col 4",
                                        "col_5": "row 1 col 5"
                                    }, {
                                        "col_18": "row 2 col 18",
                                        "col_19": "row 2 col 19",
                                        "col_14": "row 2 col 14",
                                        "col_15": "row 2 col 15",
                                        "col_16": "row 2 col 16",
                                        "col_17": "row 2 col 17",
                                        "col_10": "row 2 col 10",
                                        "col_11": "row 2 col 11",
                                        "col_12": "row 2 col 12",
                                        "col_13": "row 2 col 13",
                                        "col_8": "row 2 col 8",
                                        "col_9": "row 2 col 9",
                                        "col_2": "row 2 col 2",
                                        "col_3": "row 2 col 3",
                                        "col_0": "row 2 col 0",
                                        "col_1": "row 2 col 1",
                                        "col_6": "row 2 col 6",
                                        "col_7": "row 2 col 7",
                                        "col_4": "row 2 col 4",
                                        "col_5": "row 2 col 5"
                                    }, {
                                        "col_18": "row 3 col 18",
                                        "col_19": "row 3 col 19",
                                        "col_14": "row 3 col 14",
                                        "col_15": "row 3 col 15",
                                        "col_16": "row 3 col 16",
                                        "col_17": "row 3 col 17",
                                        "col_10": "row 3 col 10",
                                        "col_11": "row 3 col 11",
                                        "col_12": "row 3 col 12",
                                        "col_13": "row 3 col 13",
                                        "col_8": "row 3 col 8",
                                        "col_9": "row 3 col 9",
                                        "col_2": "row 3 col 2",
                                        "col_3": "row 3 col 3",
                                        "col_0": "row 3 col 0",
                                        "col_1": "row 3 col 1",
                                        "col_6": "row 3 col 6",
                                        "col_7": "row 3 col 7",
                                        "col_4": "row 3 col 4",
                                        "col_5": "row 3 col 5"
                                    }, {
                                        "col_18": "row 4 col 18",
                                        "col_19": "row 4 col 19",
                                        "col_14": "row 4 col 14",
                                        "col_15": "row 4 col 15",
                                        "col_16": "row 4 col 16",
                                        "col_17": "row 4 col 17",
                                        "col_10": "row 4 col 10",
                                        "col_11": "row 4 col 11",
                                        "col_12": "row 4 col 12",
                                        "col_13": "row 4 col 13",
                                        "col_8": "row 4 col 8",
                                        "col_9": "row 4 col 9",
                                        "col_2": "row 4 col 2",
                                        "col_3": "row 4 col 3",
                                        "col_0": "row 4 col 0",
                                        "col_1": "row 4 col 1",
                                        "col_6": "row 4 col 6",
                                        "col_7": "row 4 col 7",
                                        "col_4": "row 4 col 4",
                                        "col_5": "row 4 col 5"
                                    }, {
                                        "col_18": "row 5 col 18",
                                        "col_19": "row 5 col 19",
                                        "col_14": "row 5 col 14",
                                        "col_15": "row 5 col 15",
                                        "col_16": "row 5 col 16",
                                        "col_17": "row 5 col 17",
                                        "col_10": "row 5 col 10",
                                        "col_11": "row 5 col 11",
                                        "col_12": "row 5 col 12",
                                        "col_13": "row 5 col 13",
                                        "col_8": "row 5 col 8",
                                        "col_9": "row 5 col 9",
                                        "col_2": "row 5 col 2",
                                        "col_3": "row 5 col 3",
                                        "col_0": "row 5 col 0",
                                        "col_1": "row 5 col 1",
                                        "col_6": "row 5 col 6",
                                        "col_7": "row 5 col 7",
                                        "col_4": "row 5 col 4",
                                        "col_5": "row 5 col 5"
                                    }, {
                                        "col_18": "row 6 col 18",
                                        "col_19": "row 6 col 19",
                                        "col_14": "row 6 col 14",
                                        "col_15": "row 6 col 15",
                                        "col_16": "row 6 col 16",
                                        "col_17": "row 6 col 17",
                                        "col_10": "row 6 col 10",
                                        "col_11": "row 6 col 11",
                                        "col_12": "row 6 col 12",
                                        "col_13": "row 6 col 13",
                                        "col_8": "row 6 col 8",
                                        "col_9": "row 6 col 9",
                                        "col_2": "row 6 col 2",
                                        "col_3": "row 6 col 3",
                                        "col_0": "row 6 col 0",
                                        "col_1": "row 6 col 1",
                                        "col_6": "row 6 col 6",
                                        "col_7": "row 6 col 7",
                                        "col_4": "row 6 col 4",
                                        "col_5": "row 6 col 5"
                                    }, {
                                        "col_18": "row 7 col 18",
                                        "col_19": "row 7 col 19",
                                        "col_14": "row 7 col 14",
                                        "col_15": "row 7 col 15",
                                        "col_16": "row 7 col 16",
                                        "col_17": "row 7 col 17",
                                        "col_10": "row 7 col 10",
                                        "col_11": "row 7 col 11",
                                        "col_12": "row 7 col 12",
                                        "col_13": "row 7 col 13",
                                        "col_8": "row 7 col 8",
                                        "col_9": "row 7 col 9",
                                        "col_2": "row 7 col 2",
                                        "col_3": "row 7 col 3",
                                        "col_0": "row 7 col 0",
                                        "col_1": "row 7 col 1",
                                        "col_6": "row 7 col 6",
                                        "col_7": "row 7 col 7",
                                        "col_4": "row 7 col 4",
                                        "col_5": "row 7 col 5"
                                    }, {
                                        "col_18": "row 8 col 18",
                                        "col_19": "row 8 col 19",
                                        "col_14": "row 8 col 14",
                                        "col_15": "row 8 col 15",
                                        "col_16": "row 8 col 16",
                                        "col_17": "row 8 col 17",
                                        "col_10": "row 8 col 10",
                                        "col_11": "row 8 col 11",
                                        "col_12": "row 8 col 12",
                                        "col_13": "row 8 col 13",
                                        "col_8": "row 8 col 8",
                                        "col_9": "row 8 col 9",
                                        "col_2": "row 8 col 2",
                                        "col_3": "row 8 col 3",
                                        "col_0": "row 8 col 0",
                                        "col_1": "row 8 col 1",
                                        "col_6": "row 8 col 6",
                                        "col_7": "row 8 col 7",
                                        "col_4": "row 8 col 4",
                                        "col_5": "row 8 col 5"
                                    }, {
                                        "col_18": "row 9 col 18",
                                        "col_19": "row 9 col 19",
                                        "col_14": "row 9 col 14",
                                        "col_15": "row 9 col 15",
                                        "col_16": "row 9 col 16",
                                        "col_17": "row 9 col 17",
                                        "col_10": "row 9 col 10",
                                        "col_11": "row 9 col 11",
                                        "col_12": "row 9 col 12",
                                        "col_13": "row 9 col 13",
                                        "col_8": "row 9 col 8",
                                        "col_9": "row 9 col 9",
                                        "col_2": "row 9 col 2",
                                        "col_3": "row 9 col 3",
                                        "col_0": "row 9 col 0",
                                        "col_1": "row 9 col 1",
                                        "col_6": "row 9 col 6",
                                        "col_7": "row 9 col 7",
                                        "col_4": "row 9 col 4",
                                        "col_5": "row 9 col 5"
                                    }
                                ],
                                "type": "TableLog",
                                "utc_time": "2019-02-12T17:41:43.252162+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.262985+00:00",
                                "description": "Table Log: long cells",
                                "line_no": 504,
                                "display_index": false,
                                "meta_type": "entry",
                                "columns": ["Name", "Age", "Address"],
                                "indices": [0, 1, 2, 3, 4, 5],
                                "table": [{
                                        "Age": "33",
                                        "Name": "Bob Stevens",
                                        "Address": "89 Trinsdale Avenue, LONDON, E8 0XW"
                                    }, {
                                        "Age": "21",
                                        "Name": "Susan Evans",
                                        "Address": "100 Loop Road, SWANSEA, U8 12JK"
                                    }, {
                                        "Age": "88",
                                        "Name": "Trevor Dune",
                                        "Address": "28 Kings Lane, MANCHESTER, MT16 2YT"
                                    }, {
                                        "Age": "38",
                                        "Name": "Belinda Baggins",
                                        "Address": "31 Prospect Hill, DOYNTON, BS30 9DN"
                                    }, {
                                        "Age": "89",
                                        "Name": "Cosimo Hornblower",
                                        "Address": "65 Prospect Hill, SURREY, PH33 4TY"
                                    }, {
                                        "Age": "31",
                                        "Name": "Sabine Wurfel",
                                        "Address": "88 Clasper Way, HEXWORTHY, PL20 4BG"
                                    }
                                ],
                                "type": "TableLog",
                                "utc_time": "2019-02-12T17:41:43.262975+00:00"
                            }
                        ],
                        "uid": "78dd1eab-07f3-44b6-b94c-dafe0293ae77",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "failed",
                        "name": "test_dict_namespace",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.295194+00:00",
                                "end": "2019-02-12T17:41:43.304266+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.295236+00:00",
                                "description": "Simple dict match",
                                "comparison": [[0, "foo", "Passed", ["int", "1"], ["int", "1"]], [0, "bar", "Failed", ["int", "2"], ["int", "5"]], [0, "extra-key", "Failed", [null, "ABSENT"], ["int", "10"]]],
                                "line_no": 524,
                                "expected_description": null,
                                "actual_description": null,
                                "meta_type": "assertion",
                                "include_keys": null,
                                "passed": false,
                                "exclude_keys": null,
                                "type": "DictMatch",
                                "utc_time": "2019-02-12T17:41:43.295231+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.297024+00:00",
                                "description": "Nested dict match",
                                "comparison": [[0, "foo", "Failed", "", ""], [1, "alpha", "Failed", "", ""], [1, "", "Passed", ["int", "1"], ["int", "1"]], [1, "", "Passed", ["int", "2"], ["int", "2"]], [1, "", "Failed", ["int", "3"], [null, null]], [1, "beta", "Failed", "", ""], [2, "color", "Failed", ["str", "red"], ["str", "blue"]]],
                                "line_no": 542,
                                "expected_description": null,
                                "actual_description": null,
                                "meta_type": "assertion",
                                "include_keys": null,
                                "passed": false,
                                "exclude_keys": null,
                                "type": "DictMatch",
                                "utc_time": "2019-02-12T17:41:43.297017+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.299092+00:00",
                                "description": "Dict match: Custom comparators",
                                "comparison": [[0, "baz", "Passed", ["str", "hello world"], ["REGEX", "\\w+ world"]], [0, "foo", "Passed", "", ""], [0, "", "Passed", ["int", "1"], ["int", "1"]], [0, "", "Passed", ["int", "2"], ["int", "2"]], [0, "", "Passed", ["int", "3"], ["func", "<lambda>"]], [0, "bar", "Passed", "", ""], [1, "color", "Passed", ["str", "blue"], ["func", "VAL in ['blue', 'red', 'yellow']"]]],
                                "line_no": 560,
                                "expected_description": null,
                                "actual_description": null,
                                "meta_type": "assertion",
                                "include_keys": null,
                                "passed": true,
                                "exclude_keys": null,
                                "type": "DictMatch",
                                "utc_time": "2019-02-12T17:41:43.299084+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.300822+00:00",
                                "description": null,
                                "has_keys": ["foo", "alpha"],
                                "line_no": 570,
                                "meta_type": "assertion",
                                "absent_keys_diff": ["bar"],
                                "passed": false,
                                "has_keys_diff": ["alpha"],
                                "type": "DictCheck",
                                "absent_keys": ["bar", "beta"],
                                "utc_time": "2019-02-12T17:41:43.300815+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.302500+00:00",
                                "description": null,
                                "flattened_dict": [[0, "baz", ["str", "hello world"]], [0, "foo", ""], [0, "", ["int", "1"]], [0, "", ["int", "2"]], [0, "", ["int", "3"]], [0, "bar", ""], [1, "color", ["str", "blue"]]],
                                "line_no": 579,
                                "meta_type": "entry",
                                "type": "DictLog",
                                "utc_time": "2019-02-12T17:41:43.302494+00:00"
                            }
                        ],
                        "uid": "451c82db-0939-40c5-ae6c-b2750c6fca52",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "failed",
                        "name": "test_fix_namespace",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.309758+00:00",
                                "end": "2019-02-12T17:41:43.316489+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.309890+00:00",
                                "description": null,
                                "comparison": [[0, 555, "Failed", "", ""], [0, "", "Failed", "", ""], [1, 600, "Passed", ["str", "A"], ["str", "A"]], [1, 601, "Failed", ["str", "A"], ["str", "B"]], [1, 683, "Passed", "", ""], [1, "", "Passed", "", ""], [2, 688, "Passed", ["str", "a"], ["str", "a"]], [2, 689, "Passed", ["str", "a"], ["REGEX", "[a-z]"]], [1, "", "Passed", "", ""], [2, 688, "Passed", ["str", "b"], ["str", "b"]], [2, 689, "Passed", ["str", "b"], ["str", "b"]], [0, "", "Failed", "", ""], [1, 600, "Failed", ["str", "B"], ["str", "C"]], [1, 601, "Passed", ["str", "B"], ["str", "B"]], [1, 683, "Passed", "", ""], [1, "", "Passed", "", ""], [2, 688, "Passed", ["str", "c"], ["str", "c"]], [2, 689, "Passed", ["str", "c"], ["func", "VAL in ('c', 'd')"]], [1, "", "Passed", "", ""], [2, 688, "Passed", ["str", "d"], ["str", "d"]], [2, 689, "Passed", ["str", "d"], ["str", "d"]], [0, 36, "Passed", ["int", "6"], ["int", "6"]], [0, 38, "Passed", ["int", "5"], ["func", "VAL >= 4"]], [0, 22, "Passed", ["int", "5"], ["int", "5"]], [0, 55, "Passed", ["int", "2"], ["int", "2"]]],
                                "line_no": 667,
                                "expected_description": null,
                                "actual_description": null,
                                "meta_type": "assertion",
                                "include_keys": null,
                                "passed": false,
                                "exclude_keys": null,
                                "type": "FixMatch",
                                "utc_time": "2019-02-12T17:41:43.309884+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.312797+00:00",
                                "description": null,
                                "has_keys": [26, 22, 11],
                                "line_no": 675,
                                "meta_type": "assertion",
                                "absent_keys_diff": [555],
                                "passed": false,
                                "has_keys_diff": [26, 11],
                                "type": "FixCheck",
                                "absent_keys": [444, 555],
                                "utc_time": "2019-02-12T17:41:43.312789+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.314860+00:00",
                                "description": null,
                                "flattened_dict": [[0, 555, ""], [0, "", ""], [1, 624, ["int", "1"]], [1, 556, ["str", "USD"]], [0, "", ""], [1, 624, ["int", "2"]], [1, 556, ["str", "EUR"]], [0, 36, ["int", "6"]], [0, 38, ["int", "5"]], [0, 22, ["int", "5"]], [0, 55, ["int", "2"]]],
                                "line_no": 688,
                                "meta_type": "entry",
                                "type": "FixLog",
                                "utc_time": "2019-02-12T17:41:43.314849+00:00"
                            }
                        ],
                        "uid": "7b72fe93-ef07-4ed8-bc9a-114a8cc0ff4f",
                        "type": "TestCaseReport",
                        "logs": []
                    }, {
                        "status": "passed",
                        "name": "test_xml_namespace",
                        "tags": {},
                        "description": null,
                        "timer": {
                            "run": {
                                "start": "2019-02-12T17:41:43.321328+00:00",
                                "end": "2019-02-12T17:41:43.327366+00:00"
                            }
                        },
                        "suite_related": false,
                        "status_override": null,
                        "entries": [{
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.321541+00:00",
                                "description": "Simple XML check for existence of xpath.",
                                "xpath": "/Root/Test",
                                "xml": "<Root>\n                <Test>Foo</Test>\n            </Root>\n",
                                "data": [],
                                "line_no": 710,
                                "tags": null,
                                "meta_type": "assertion",
                                "passed": true,
                                "message": "xpath: `/Root/Test` exists in the XML.",
                                "type": "XMLCheck",
                                "namespaces": null,
                                "utc_time": "2019-02-12T17:41:43.321534+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.323547+00:00",
                                "description": "XML check for tags in the given xpath.",
                                "xpath": "/Root/Test",
                                "xml": "<Root>\n                <Test>Value1</Test>\n                <Test>Value2</Test>\n            </Root>\n",
                                "data": [["Value1", null, null, null], ["Value2", null, null, null]],
                                "line_no": 724,
                                "tags": ["Value1", "Value2"],
                                "meta_type": "assertion",
                                "passed": true,
                                "message": null,
                                "type": "XMLCheck",
                                "namespaces": null,
                                "utc_time": "2019-02-12T17:41:43.323539+00:00"
                            }, {
                                "category": "DEFAULT",
                                "machine_time": "2019-02-12T17:41:43.325653+00:00",
                                "description": "XML check with namespace matching.",
                                "xpath": "//*/a:message",
                                "xml": "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\">\n                <SOAP-ENV:Header/>\n                <SOAP-ENV:Body>\n                    <ns0:message xmlns:ns0=\"http://testplan\">Hello world!</ns0:message>\n                </SOAP-ENV:Body>\n            </SOAP-ENV:Envelope>\n",
                                "data": [["Hello world!", null, null, "REGEX(Hello*)"]],
                                "line_no": 743,
                                "tags": ["<_sre.SRE_Pattern object at 0x7f163091e030>"],
                                "meta_type": "assertion",
                                "passed": true,
                                "message": null,
                                "type": "XMLCheck",
                                "namespaces": {
                                    "a": "http://testplan"
                                },
                                "utc_time": "2019-02-12T17:41:43.325645+00:00"
                            }
                        ],
                        "uid": "0d45f100-da7b-46be-a6a5-3188c425b764",
                        "type": "TestCaseReport",
                        "logs": []
                    }
                ],
                "uid": "c01e19ca-dfdc-4c34-9b0f-a28b9acd896a",
                "type": "TestGroupReport",
                "logs": []
            }
        ],
        "uid": "0c10b29b-7cc2-4ebb-a25c-e44e991f21f3",
        "type": "TestGroupReport",
        "logs": []
    }
], "name": "Assertions Example"
};


export {
  TESTPLAN_REPORT,
  fakeReportAssertions,
}