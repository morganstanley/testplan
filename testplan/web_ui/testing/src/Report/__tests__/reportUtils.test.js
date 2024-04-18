import React from "react";

import { TESTPLAN_REPORT } from "../../Common/sampleReports";
import { PropagateIndices, MergeSplittedReport } from "../reportUtils";

describe("Report/reportUtils", () => {
  describe("PropagateIndices", () => {
    let report;
    let multitest;
    let suiteA;
    let suiteB;
    let testcase;
    let testplanEntries = {};

    beforeEach(() => {
      report = PropagateIndices(TESTPLAN_REPORT);
      multitest = report.entries[0];
      suiteA = multitest.entries[0];
      suiteB = multitest.entries[1];
      testcase = suiteA.entries[0];
      testplanEntries = {
        testplan: report,
        multitest: multitest,
        testsuite: suiteA,
        testcase: testcase,
      };
    });

    afterEach(() => {
      report = undefined;
      multitest = undefined;
      suiteA = undefined;
      suiteB = undefined;
      testcase = undefined;
      testplanEntries = {};
    });

    it(
      "tags - exact same tags on parent & child don't appear twice in " +
        "child's tags",
      () => {
        expect(multitest.tags).toEqual(suiteA.tags);
      }
    );

    it(
      "tags - parent & child with same named tags but different values " +
        "extend the child tag's list",
      () => {
        const expected = {
          simple: ["server", "client"],
        };
        expect(suiteB.tags).toEqual(expected);
      }
    );

    it(
      "tags - parent & child with different named tags both appear in " +
        "child tags",
      () => {
        const expected = {
          simple: ["server"],
          colour: ["white"],
        };
        expect(testcase.tags).toEqual(expected);
      }
    );

    it("tags_index - stores parent tags & descendent's tags", () => {
      const expected = {
        simple: ["server", "client"],
        colour: ["white"],
      };
      expect(multitest.tags_index).toEqual(expected);
    });

    [
      [
        "testplan",
        [
          "Sample Testplan|testplan",
          "Primary|multitest",
          "AlphaSuite|testsuite",
          "test_equality_passing|testcase",
          "test_equality_passing2|testcase",
          "BetaSuite|testsuite",
          "Secondary|multitest",
          "GammaSuite|testsuite",
        ],
      ],
      [
        "multitest",
        [
          "Primary|multitest",
          "Sample Testplan|testplan",
          "AlphaSuite|testsuite",
          "test_equality_passing|testcase",
          "test_equality_passing2|testcase",
          "BetaSuite|testsuite",
        ],
      ],
      [
        "testsuite",
        [
          "AlphaSuite|testsuite",
          "Primary|multitest",
          "Sample Testplan|testplan",
          "test_equality_passing|testcase",
          "test_equality_passing2|testcase",
        ],
      ],
      [
        "testcase",
        [
          "test_equality_passing|testcase",
          "AlphaSuite|testsuite",
          "Primary|multitest",
          "Sample Testplan|testplan",
        ],
      ],
    ].forEach(([entryType, nameTypeIndex]) => {
      it(
        `${entryType} name_type_index - stores ancestors & ` +
          "descendents names & types",
        () => {
          const entry = testplanEntries[entryType];
          expect(entry.name_type_index).toEqual(nameTypeIndex);
        }
      );
    });
  });

  it("Merge splitted JSON report", () => {
    const mainReport = {
      python_version: "3.7.1",
      category: "testplan",
      version: 2,
      runtime_status: "finished",
      status: "failed",
      entries: [],
      name: "Multiply",
      uid: "Multiply",
      project: "testplan",
      timeout: 14400,
    };

    const assertions = {
      basic_multiply__p1_aaaa__p2_11111: [
        { name: "test assertion1", uid: "test_assertion1" },
      ],
      basic_multiply__p1_bbbb__p2_22222: [
        { name: "test assertion2", uid: "test_assertion2" },
      ],
    };

    const structure = [
      {
        category: "multitest",
        parent_uids: ["Multiply"],
        name: "MultiplyTest",
        uid: "MultiplyTest",
        entries: [
          {
            category: "testsuite",
            parent_uids: ["Multiply", "MultiplyTest"],
            name: "BasicSuite",
            uid: "BasicSuite",
            entries: [
              {
                category: "parametrization",
                parent_uids: ["Multiply", "MultiplyTest", "BasicSuite"],
                name: "Basic Multiply",
                uid: "basic_multiply",
                entries: [
                  {
                    entries: [],
                    type: "TestCaseReport",
                    category: "testcase",
                    parent_uids: [
                      "Multiply",
                      "MultiplyTest",
                      "BasicSuite",
                      "basic_multiply",
                    ],
                    name: "basic multiply <p1='aaaa', p2=11111>",
                    uid: "basic_multiply__p1_aaaa__p2_11111",
                  },
                  {
                    entries: [],
                    type: "TestCaseReport",
                    category: "testcase",
                    parent_uids: [
                      "Multiply",
                      "MultiplyTest",
                      "BasicSuite",
                      "basic_multiply",
                    ],
                    name: "basic multiply <p1='bbbb', p2=22222>",
                    uid: "basic_multiply__p1_bbbb__p2_22222",
                  },
                ],
                type: "TestGroupReport",
              },
            ],
            type: "TestGroupReport",
          },
        ],
        type: "TestGroupReport",
      },
    ];

    const expected = {
      python_version: "3.7.1",
      category: "testplan",
      version: 2,
      runtime_status: "finished",
      status: "failed",
      entries: [
        {
          category: "multitest",
          parent_uids: ["Multiply"],
          name: "MultiplyTest",
          uid: "MultiplyTest",
          entries: [
            {
              category: "testsuite",
              parent_uids: ["Multiply", "MultiplyTest"],
              name: "BasicSuite",
              uid: "BasicSuite",
              entries: [
                {
                  category: "parametrization",
                  parent_uids: ["Multiply", "MultiplyTest", "BasicSuite"],
                  name: "Basic Multiply",
                  uid: "basic_multiply",
                  entries: [
                    {
                      entries: [
                        { name: "test assertion1", uid: "test_assertion1" },
                      ],
                      type: "TestCaseReport",
                      category: "testcase",
                      parent_uids: [
                        "Multiply",
                        "MultiplyTest",
                        "BasicSuite",
                        "basic_multiply",
                      ],
                      name: "basic multiply <p1='aaaa', p2=11111>",
                      uid: "basic_multiply__p1_aaaa__p2_11111",
                    },
                    {
                      entries: [
                        { name: "test assertion2", uid: "test_assertion2" },
                      ],
                      type: "TestCaseReport",
                      category: "testcase",
                      parent_uids: [
                        "Multiply",
                        "MultiplyTest",
                        "BasicSuite",
                        "basic_multiply",
                      ],
                      name: "basic multiply <p1='bbbb', p2=22222>",
                      uid: "basic_multiply__p1_bbbb__p2_22222",
                    },
                  ],
                  type: "TestGroupReport",
                },
              ],
              type: "TestGroupReport",
            },
          ],
          type: "TestGroupReport",
        },
      ],
      name: "Multiply",
      uid: "Multiply",
      project: "testplan",
      timeout: 14400,
    };
    const resultReport = MergeSplittedReport(mainReport, assertions, structure);
    expect(resultReport).toEqual(expected);
  });
});
