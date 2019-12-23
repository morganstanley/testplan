import React from 'react';

import {TESTPLAN_REPORT} from "../../Common/sampleReports";
import {PropagateIndices} from "../reportUtils";

describe('Report/reportUtils', () => {

  describe('PropagateIndices', () => {

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

    it('tags - exact same tags on parent & child don\'t appear twice in ' +
       'child\'s tags', () => {
      expect(multitest.tags).toEqual(suiteA.tags);
    });

    it('tags - parent & child with same named tags but different values ' +
       'extend the child tag\'s list', () => {
      const expected = {
        simple: ['server', 'client'],
      };
      expect(suiteB.tags).toEqual(expected);
    });

    it('tags - parent & child with different named tags both appear in ' +
       'child tags', () => {
      const expected = {
        simple: ['server'],
        colour: ['white'],
      };
      expect(testcase.tags).toEqual(expected);
    });

    it('tags_index - stores parent tags & descendent\'s tags', () => {
      const expected = {
        simple: ['server', 'client'],
        colour: ['white'],
      };
      expect(multitest.tags_index).toEqual(expected);
    });

    [
      [
        'testplan',
        new Set([
          'Sample Testplan|testplan',
          'Primary|multitest',
          'AlphaSuite|testsuite',
          'test_equality_passing|testcase',
          'test_equality_passing2|testcase',
          'BetaSuite|testsuite',
          'Secondary|multitest',
          'GammaSuite|testsuite',
      ]),
      ],
      [
        'multitest',
        new Set([
          'Primary|multitest',
          'Sample Testplan|testplan',
          'AlphaSuite|testsuite',
          'test_equality_passing|testcase',
          'test_equality_passing2|testcase',
          'BetaSuite|testsuite',
        ]),
      ],
      [
        'testsuite',
        new Set([
          'AlphaSuite|testsuite',
          'Primary|multitest',
          'Sample Testplan|testplan',
          'test_equality_passing|testcase',
          'test_equality_passing2|testcase',
        ]),
      ],
      [
        'testcase',
        new Set([
          'test_equality_passing|testcase',
          'AlphaSuite|testsuite',
          'Primary|multitest',
          'Sample Testplan|testplan',
        ]),
      ],
    ].forEach(([entryType, nameTypeIndex]) => {
      it(`${entryType} name_type_index - stores ancestors & ` +
         'descendents names & types', () => {
        const entry = testplanEntries[entryType];
        expect(entry.name_type_index).toEqual(nameTypeIndex);
      });
    });

    [
      ['testplan', {passed: 3, failed: 1}],
      ['multitest', {passed: 2, failed: 1}],
      ['testsuite', {passed: 1, failed: 1}],
      ['testcase', {passed: 1, failed: 0}],
    ].forEach(([entryType, caseCount]) => {
      it(`${entryType} case_count - stores number of passing & failing ` +
         'testcases within entry', () => {
        const entry = testplanEntries[entryType];
        expect(entry.case_count).toEqual(caseCount);
      });
    });

  });

});
