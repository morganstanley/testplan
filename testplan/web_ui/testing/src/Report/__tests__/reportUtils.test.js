import React from "react";

import { TESTPLAN_REPORT } from "../../Common/sampleReports";
import {
  PropagateIndices,
  MergeSplittedReport,
  applyPartsMerge,
} from "../reportUtils";

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

  describe("applyPartsMerge", () => {
    const createPart = (partIndex, totalParts, overrides = {}) => ({
      uid: `multitest_part${partIndex}`,
      name: `MyMultitest - part ${partIndex}/${totalParts}`,
      definition_name: "MyMultitest",
      category: "multitest",
      part: [partIndex, totalParts],
      status: "passed",
      counter: { passed: 1, failed: 0, total: 1, error: 0 },
      timer: { run: [{ start: "2024-01-01T00:00:00", end: "2024-01-01T00:01:00" }] },
      tags: {},
      logs: [],
      entries: [],
      ...overrides,
    });

    const createSuite = (name, overrides = {}) => ({
      uid: `suite_${name}`,
      name,
      definition_name: name,
      category: "testsuite",
      status: "passed",
      counter: { passed: 1, failed: 0, total: 1, error: 0 },
      timer: {},
      tags: {},
      logs: [],
      entries: [],
      ...overrides,
    });

    const createTestCase = (name, uid, status = "passed") => ({
      uid,
      name,
      definition_name: name,
      category: "testcase",
      type: "TestCaseReport",
      status,
      counter: {
        passed: status === "passed" ? 1 : 0,
        failed: status === "failed" ? 1 : 0,
        total: 1,
        error: status === "error" ? 1 : 0,
      },
      entries: [],
    });

    const createParametrization = (name, overrides = {}) => ({
      uid: `param_${name}`,
      name,
      definition_name: name,
      category: "parametrization",
      type: "TestGroupReport",
      status: "passed",
      counter: { passed: 1, failed: 0, total: 1, error: 0 },
      timer: {},
      tags: {},
      logs: [],
      entries: [],
      ...overrides,
    });

    it("does not merge entries without part field", () => {
      const report = {
        uid: "testplan",
        entries: [
          { uid: "mt1", name: "Multitest1", definition_name: "Multitest1" },
          { uid: "mt2", name: "Multitest2", definition_name: "Multitest2" },
        ],
      };
      const result = applyPartsMerge(report);
      expect(result.entries).toHaveLength(2);
      expect(result.entries[0].uid).toBe("mt1");
      expect(result.entries[1].uid).toBe("mt2");
    });

    it("merges two parts with same definition_name", () => {
      const part0 = createPart(0, 2, {
        entries: [createSuite("SuiteA")],
        counter: { passed: 2, failed: 0, total: 2, error: 0 },
      });
      const part1 = createPart(1, 2, {
        entries: [createSuite("SuiteB")],
        counter: { passed: 2, failed: 1, total: 3, error: 0 },
      });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      expect(result.entries).toHaveLength(1);
      const merged = result.entries[0];
      expect(merged.name).toBe("MyMultitest [Merged]");
      expect(merged.part).toBeNull();
      expect(merged._allPartUids).toEqual([
        "multitest_part0",
        "multitest_part1",
      ]);
      expect(merged.counter).toEqual({
        passed: 4,
        failed: 1,
        total: 5,
        error: 0,
      });
    });

    it("preserves order when mixing parts and non-parts", () => {
      const standalone = {
        uid: "standalone",
        name: "Standalone",
        definition_name: "Standalone",
      };
      const part0 = createPart(0, 2);
      const part1 = createPart(1, 2);

      const report = {
        uid: "testplan",
        entries: [part0, part1, standalone],
      };
      const result = applyPartsMerge(report);

      expect(result.entries).toHaveLength(2);
      expect(result.entries[0].name).toBe("MyMultitest [Merged]");
      expect(result.entries[1].name).toBe("Standalone");
    });

    it("merges counters correctly", () => {
      const part0 = createPart(0, 2, {
        counter: { passed: 5, failed: 2, total: 7, error: 1 },
      });
      const part1 = createPart(1, 2, {
        counter: { passed: 3, failed: 1, total: 4, error: 0 },
      });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      expect(result.entries[0].counter).toEqual({
        passed: 8,
        failed: 3,
        total: 11,
        error: 1,
      });
    });

    it("merges status with correct priority (error > failed > passed)", () => {
      const part0 = createPart(0, 2, { status: "passed" });
      const part1 = createPart(1, 2, { status: "failed" });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      expect(result.entries[0].status).toBe("failed");
    });

    it("tags entries with _sourceMultitestUid", () => {
      const suite = createSuite("SuiteA");
      const part0 = createPart(0, 1, { entries: [suite] });

      const report = { uid: "testplan", entries: [part0] };
      const result = applyPartsMerge(report);

      const mergedSuite = result.entries[0].entries[0];
      expect(mergedSuite._sourceMultitestUid).toBe("multitest_part0");
    });

    it("filters out synthesized entries", () => {
      const suite = createSuite("SuiteA");
      const synthesized = {
        uid: "env_start",
        category: "synthesized",
        name: "Environment Start",
      };
      const part0 = createPart(0, 1, { entries: [synthesized, suite] });

      const report = { uid: "testplan", entries: [part0] };
      const result = applyPartsMerge(report);

      expect(result.entries[0].entries).toHaveLength(1);
      expect(result.entries[0].entries[0].name).toBe("SuiteA");
    });

    it("does not mutate original report", () => {
      const part0 = createPart(0, 2);
      const part1 = createPart(1, 2);
      const report = { uid: "testplan", entries: [part0, part1] };

      const originalEntries = [...report.entries];
      applyPartsMerge(report);

      expect(report.entries).toEqual(originalEntries);
      expect(report.entries).toHaveLength(2);
    });

    it("merges _allPartUids for duplicate suites from different parts", () => {
      const suiteA_part0 = createSuite("SuiteA", { uid: "suiteA_part0" });
      const suiteA_part1 = createSuite("SuiteA", { uid: "suiteA_part1" });
      const part0 = createPart(0, 2, { entries: [suiteA_part0] });
      const part1 = createPart(1, 2, { entries: [suiteA_part1] });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      const mergedSuite = result.entries[0].entries[0];
      expect(mergedSuite.uid).toBe("suiteA_part0");
      expect(mergedSuite._allPartUids).toEqual(["suiteA_part0", "suiteA_part1"]);
    });

    it("merges counters and status for duplicate suites", () => {
      const suiteA_part0 = createSuite("SuiteA", {
        uid: "suiteA_part0",
        counter: { passed: 2, failed: 1, total: 3, error: 0 },
        status: "failed",
      });
      const suiteA_part1 = createSuite("SuiteA", {
        uid: "suiteA_part1",
        counter: { passed: 1, failed: 0, total: 1, error: 1 },
        status: "error",
      });
      const part0 = createPart(0, 2, { entries: [suiteA_part0] });
      const part1 = createPart(1, 2, { entries: [suiteA_part1] });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      const mergedSuite = result.entries[0].entries[0];
      expect(mergedSuite.counter).toEqual({
        passed: 3,
        failed: 1,
        total: 4,
        error: 1,
      });
      expect(mergedSuite.status).toBe("error");
    });

    it("preserves test cases from all parts under merged suite", () => {
      const suiteA_part0 = createSuite("SuiteA", {
        uid: "suiteA_part0",
        entries: [createTestCase("test1", "test1_uid")],
      });
      const suiteA_part1 = createSuite("SuiteA", {
        uid: "suiteA_part1",
        entries: [createTestCase("test2", "test2_uid")],
      });
      const part0 = createPart(0, 2, { entries: [suiteA_part0] });
      const part1 = createPart(1, 2, { entries: [suiteA_part1] });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      const mergedSuite = result.entries[0].entries[0];
      expect(mergedSuite.entries).toHaveLength(2);
      expect(mergedSuite.entries[0].uid).toBe("test1_uid");
      expect(mergedSuite.entries[1].uid).toBe("test2_uid");
    });

    it("test cases retain _sourceMultitestUid for assertion lookup", () => {
      const suiteA_part0 = createSuite("SuiteA", {
        uid: "suiteA_part0",
        entries: [createTestCase("test1", "test1_uid")],
      });
      const suiteA_part1 = createSuite("SuiteA", {
        uid: "suiteA_part1",
        entries: [createTestCase("test2", "test2_uid")],
      });
      const part0 = createPart(0, 2, { entries: [suiteA_part0] });
      const part1 = createPart(1, 2, { entries: [suiteA_part1] });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      const mergedSuite = result.entries[0].entries[0];
      expect(mergedSuite.entries[0]._sourceMultitestUid).toBe("multitest_part0");
      expect(mergedSuite.entries[1]._sourceMultitestUid).toBe("multitest_part1");
    });

    it("merges three or more parts correctly", () => {
      const part0 = createPart(0, 3, {
        entries: [createSuite("SuiteA", { uid: "suiteA_p0" })],
        counter: { passed: 1, failed: 0, total: 1 },
      });
      const part1 = createPart(1, 3, {
        entries: [createSuite("SuiteB", { uid: "suiteB_p1" })],
        counter: { passed: 2, failed: 0, total: 2 },
      });
      const part2 = createPart(2, 3, {
        entries: [createSuite("SuiteC", { uid: "suiteC_p2" })],
        counter: { passed: 3, failed: 1, total: 4 },
      });

      const report = { uid: "testplan", entries: [part0, part1, part2] };
      const result = applyPartsMerge(report);

      expect(result.entries).toHaveLength(1);
      const merged = result.entries[0];
      expect(merged.name).toBe("MyMultitest [Merged]");
      expect(merged.part).toBeNull();
      expect(merged._allPartUids).toEqual([
        "multitest_part0",
        "multitest_part1",
        "multitest_part2",
      ]);
      expect(merged.counter).toEqual({
        passed: 6,
        failed: 1,
        total: 7,
        error: 0,
      });
      expect(merged.entries).toHaveLength(3);
    });

    it("merges suites with test cases distributed across parts", () => {
      const suite0_part0 = createSuite("Suite0", {
        uid: "suite0_p0",
        entries: [createTestCase("case0", "case0_uid")],
        counter: { passed: 1, failed: 0, total: 1, error: 0 },
      });
      const suite1_part0 = createSuite("Suite1", {
        uid: "suite1_p0",
        entries: [createTestCase("case2", "case2_uid")],
        counter: { passed: 1, failed: 0, total: 1, error: 0 },
      });
      const suite1_part1 = createSuite("Suite1", {
        uid: "suite1_p1",
        entries: [
          createTestCase("case1", "case1_uid"),
          createTestCase("case3", "case3_uid"),
        ],
        counter: { passed: 2, failed: 0, total: 2, error: 0 },
      });

      const part0 = createPart(0, 2, {
        entries: [suite0_part0, suite1_part0],
        counter: { passed: 2, failed: 0, total: 2, error: 0 },
      });
      const part1 = createPart(1, 2, {
        entries: [suite1_part1],
        counter: { passed: 2, failed: 0, total: 2, error: 0 },
      });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      expect(result.entries).toHaveLength(1);
      const merged = result.entries[0];
      expect(merged.entries).toHaveLength(2);

      const mergedSuite0 = merged.entries[0];
      expect(mergedSuite0.entries).toHaveLength(1);
      expect(mergedSuite0.entries[0].uid).toBe("case0_uid");

      const mergedSuite1 = merged.entries[1];
      expect(mergedSuite1.entries).toHaveLength(3);
      expect(mergedSuite1.entries.map((e) => e.uid)).toEqual([
        "case1_uid",
        "case2_uid",
        "case3_uid",
      ]);
      expect(mergedSuite1.counter).toEqual({
        passed: 3,
        failed: 0,
        total: 3,
        error: 0,
      });
      expect(mergedSuite1._allPartUids).toEqual(["suite1_p1", "suite1_p0"]);
    });

    it("merges deeply nested suites and parametrizations", () => {
      const suiteA_part0 = createSuite("SuiteA", {
        uid: "suiteA_p0",
        entries: [
          createParametrization("ParamGroup", {
            uid: "param_p0",
            entries: [createTestCase("test <x=1>", "test_x1")],
          }),
        ],
      });

      const suiteA_part1 = createSuite("SuiteA", {
        uid: "suiteA_p1",
        entries: [
          createParametrization("ParamGroup", {
            uid: "param_p1",
            entries: [createTestCase("test <x=2>", "test_x2")],
          }),
        ],
      });

      const part0 = createPart(0, 2, { entries: [suiteA_part0] });
      const part1 = createPart(1, 2, { entries: [suiteA_part1] });

      const report = { uid: "testplan", entries: [part0, part1] };
      const result = applyPartsMerge(report);

      expect(result.entries).toHaveLength(1);
      const mergedMultitest = result.entries[0];
      expect(mergedMultitest.entries).toHaveLength(1);

      const mergedSuite = mergedMultitest.entries[0];
      expect(mergedSuite.definition_name).toBe("SuiteA");
      expect(mergedSuite.entries).toHaveLength(1);

      const mergedParam = mergedSuite.entries[0];
      expect(mergedParam.definition_name).toBe("ParamGroup");
      expect(mergedParam.entries).toHaveLength(2);
      expect(mergedParam.entries[0].uid).toBe("test_x1");
      expect(mergedParam.entries[1].uid).toBe("test_x2");
    });
  });
});
