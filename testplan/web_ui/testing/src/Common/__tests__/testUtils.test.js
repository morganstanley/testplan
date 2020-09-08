/** @jest-environment node */
import { randomSamples } from '../testUtils';
import { getPaths } from '../testUtils';
import { reverseMap } from '../testUtils';
import { filterObjectDeep } from '../testUtils';
import { deriveURLPathsFromReport } from '../testUtils';
import { TESTPLAN_REPORT } from '../fakeReport';

describe('randomSamples', () => {

  const arr = [ 111, 'bBb', new Map([ [ 'CcC', 33 ] ]), { 'd-d': 4 } ];

  it('takes the correct number of samples', () => {
    // default n=1
    expect(randomSamples(arr)).toHaveLength(1);
    expect(randomSamples(arr, 3)).toHaveLength(3);
  });

  it('takes samples of the correct size', () => {
    // default n=1, minSz=1, maxSz=`arr.length`
    const randArr1 = randomSamples(arr);
    expect(randArr1).toHaveLength(1);
    expect(randArr1[0]).toBeInstanceOf(Array);
    expect(randArr1[0].length).toBeGreaterThanOrEqual(1);
    expect(randArr1[0].length).toBeLessThanOrEqual(arr.length);

    const n = 2, minSz = 2, maxSz = 3;
    const randArr2 = randomSamples(arr, n, minSz, maxSz);
    expect(randArr2).toHaveLength(2);
    for(const sample of randArr2) {
      expect(sample).toBeInstanceOf(Array);
      expect(sample.length).toBeGreaterThanOrEqual(minSz);
      expect(sample.length).toBeLessThanOrEqual(maxSz);
    }

  });

});

const TESTPLAN_REPORT_SLIM = filterObjectDeep(
  TESTPLAN_REPORT,
  [ 'name', 'entries', 'category' ],
);

it('`filterObjectDeep` can replicate the jsdoc example', () => {
  expect(TESTPLAN_REPORT_SLIM).toEqual({
    name: "Sample Testplan",
    entries: [
      {
        name: "Primary",
        category: "multitest",
        entries: [
          {
            category: "testsuite",
            name: "AlphaSuite",
            entries: [
              {
                name: "test_equality_passing",
                category: "testcase",
                entries: [
                  {
                    category: "DEFAULT",
                  },
                ],
              },
              {
                name: "test_equality_passing2",
                category: "testcase",
                entries: [
                  {
                    category: "DEFAULT",
                  },
                ],
              },
            ],
          },
          {
            category: "testsuite",
            name: "BetaSuite",
            entries: [
              {
                name: "test_equality_passing",
                category: "testcase",
                entries: [
                  {
                    category: "DEFAULT",
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        name: "Secondary",
        category: "multitest",
        entries: [
          {
            category: "testsuite",
            name: "GammaSuite",
            entries: [
              {
                name: "test_equality_passing",
                category: "testcase",
                entries: [
                  {
                    category: "DEFAULT",
                  },
                ],
              },
            ],
          },
        ],
      },
    ],
  });
});

it('`getPaths` can replicate the jsdoc example', () => {
  const TESTPLAN_REPORT_SLIM_PATH_STRINGS = getPaths(TESTPLAN_REPORT_SLIM);
  expect(TESTPLAN_REPORT_SLIM_PATH_STRINGS).toEqual([
    'name',
    'entries',
    'entries[0]',
    'entries[0].name',
    'entries[0].category',
    'entries[0].entries',
    'entries[0].entries[0]',
    'entries[0].entries[0].category',
    'entries[0].entries[0].name',
    'entries[0].entries[0].entries',
    'entries[0].entries[0].entries[0]',
    'entries[0].entries[0].entries[0].name',
    'entries[0].entries[0].entries[0].category',
    'entries[0].entries[0].entries[0].entries',
    'entries[0].entries[0].entries[0].entries[0]',
    'entries[0].entries[0].entries[0].entries[0].category',
    'entries[0].entries[0].entries[1]',
    'entries[0].entries[0].entries[1].name',
    'entries[0].entries[0].entries[1].category',
    'entries[0].entries[0].entries[1].entries',
    'entries[0].entries[0].entries[1].entries[0]',
    'entries[0].entries[0].entries[1].entries[0].category',
    'entries[0].entries[1]',
    'entries[0].entries[1].category',
    'entries[0].entries[1].name',
    'entries[0].entries[1].entries',
    'entries[0].entries[1].entries[0]',
    'entries[0].entries[1].entries[0].name',
    'entries[0].entries[1].entries[0].category',
    'entries[0].entries[1].entries[0].entries',
    'entries[0].entries[1].entries[0].entries[0]',
    'entries[0].entries[1].entries[0].entries[0].category',
    'entries[1]',
    'entries[1].name',
    'entries[1].category',
    'entries[1].entries',
    'entries[1].entries[0]',
    'entries[1].entries[0].category',
    'entries[1].entries[0].name',
    'entries[1].entries[0].entries',
    'entries[1].entries[0].entries[0]',
    'entries[1].entries[0].entries[0].name',
    'entries[1].entries[0].entries[0].category',
    'entries[1].entries[0].entries[0].entries',
    'entries[1].entries[0].entries[0].entries[0]',
    'entries[1].entries[0].entries[0].entries[0].category',
  ]);

  const TESTPLAN_REPORT_SLIM_PATH_ARRAYS = getPaths(TESTPLAN_REPORT_SLIM, true);
  expect(TESTPLAN_REPORT_SLIM_PATH_ARRAYS).toEqual([
    [ 'name' ],
    [ 'entries' ],
    [ 'entries', '0' ],
    [ 'entries', '0', 'name' ],
    [ 'entries', '0', 'category' ],
    [ 'entries', '0', 'entries' ],
    [ 'entries', '0', 'entries', '0' ],
    [ 'entries', '0', 'entries', '0', 'category' ],
    [ 'entries', '0', 'entries', '0', 'name' ],
    [ 'entries', '0', 'entries', '0', 'entries' ],
    [ 'entries', '0', 'entries', '0', 'entries', '0' ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'name',
    ],
    [ 'entries', '0', 'entries', '0', 'entries', '0', 'category' ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'entries',
    ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'entries', '0',
    ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'category',
    ],
    [ 'entries', '0', 'entries', '0', 'entries', '1' ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '1',
      'name',
    ],
    [ 'entries', '0', 'entries', '0', 'entries', '1', 'category' ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '1',
      'entries',
    ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '1',
      'entries', '0',
    ],
    [
      'entries', '0',
      'entries', '0',
      'entries', '1',
      'entries', '0',
      'category',
    ],
    [ 'entries', '0', 'entries', '1' ],
    [ 'entries', '0', 'entries', '1', 'category' ],
    [ 'entries', '0', 'entries', '1', 'name' ],
    [ 'entries', '0', 'entries', '1', 'entries' ],
    [ 'entries', '0', 'entries', '1', 'entries', '0' ],
    [
      'entries', '0',
      'entries', '1',
      'entries', '0',
      'name',
    ],
    [ 'entries', '0', 'entries', '1', 'entries', '0', 'category' ],
    [
      'entries', '0',
      'entries', '1',
      'entries', '0',
      'entries',
    ],
    [
      'entries', '0',
      'entries', '1',
      'entries', '0',
      'entries', '0',
    ],
    [
      'entries', '0',
      'entries', '1',
      'entries', '0',
      'entries', '0',
      'category',
    ],
    [ 'entries', '1' ],
    [ 'entries', '1', 'name' ],
    [ 'entries', '1', 'category' ],
    [ 'entries', '1', 'entries' ],
    [ 'entries', '1', 'entries', '0' ],
    [ 'entries', '1', 'entries', '0', 'category' ],
    [ 'entries', '1', 'entries', '0', 'name' ],
    [ 'entries', '1', 'entries', '0', 'entries' ],
    [ 'entries', '1', 'entries', '0', 'entries', '0' ],
    [
      'entries', '1',
      'entries', '0',
      'entries', '0',
      'name',
    ],
    [ 'entries', '1', 'entries', '0', 'entries', '0', 'category' ],
    [
      'entries', '1',
      'entries', '0',
      'entries', '0',
      'entries',
    ],
    [
      'entries', '1',
      'entries', '0',
      'entries', '0',
      'entries', '0',
    ],
    [
      'entries', '1',
      'entries', '0',
      'entries', '0',
      'entries', '0',
      'category',
    ],
  ]);
});

describe('reverseMap', () => {

  const aMap = new Map([
    [ 'a', 1 ],
    [ 'b', 2 ],
    [ 'c', 3 ],
  ]);

  const aRevMap = new Map([
    [ 1, 'a' ],
    [ 2, 'b' ],
    [ 3, 'c' ],
  ]);

  it('reverses a map', () => {
    expect(reverseMap(aMap)).toStrictEqual(aRevMap);
  });
});

describe('deriveURLPathsFromReport', () => {

  it('does the jsdoc example', () => {
    const aliasMap = new Map();
    const path2PathArrayMap = new Map();
    const expectedPaths = deriveURLPathsFromReport(
      TESTPLAN_REPORT, aliasMap, path2PathArrayMap,
    );
    expect(expectedPaths).toEqual([
      '/Sample%20Testplan',
      '/Sample%20Testplan/Primary',
      '/Sample%20Testplan/Primary/AlphaSuite',
      '/Sample%20Testplan/Primary/AlphaSuite/test_equality_passing',
      '/Sample%20Testplan/Primary/AlphaSuite/test_equality_passing2',
      '/Sample%20Testplan/Primary/BetaSuite',
      '/Sample%20Testplan/Primary/BetaSuite/test_equality_passing',
      '/Sample%20Testplan/Secondary',
      '/Sample%20Testplan/Secondary/GammaSuite',
      '/Sample%20Testplan/Secondary/GammaSuite/test_equality_passing',
    ]);
    expect(aliasMap).toStrictEqual(new Map([
      [ 'Sample%20Testplan', 'Sample Testplan' ],
      [ 'Primary', 'Primary' ],
      [ 'AlphaSuite', 'AlphaSuite' ],
      [ 'test_equality_passing', 'test_equality_passing' ],
      [ 'test_equality_passing2', 'test_equality_passing2' ],
      [ 'BetaSuite', 'BetaSuite' ],
      [ 'Secondary', 'Secondary' ],
      [ 'GammaSuite', 'GammaSuite' ],
    ]));
    expect(path2PathArrayMap).toEqual(new Map([
      [ '/Sample%20Testplan', [ 'Sample Testplan' ] ],
      [ '/Sample%20Testplan/Primary', [ 'Sample Testplan', 'Primary' ] ],
      [
        '/Sample%20Testplan/Primary/AlphaSuite',
        [ 'Sample Testplan', 'Primary', 'AlphaSuite' ],
      ],
      [
        '/Sample%20Testplan/Primary/AlphaSuite/test_equality_passing',
        [
          'Sample Testplan',
          'Primary',
          'AlphaSuite',
          'test_equality_passing',
        ],
      ],
      [
        '/Sample%20Testplan/Primary/AlphaSuite/test_equality_passing2', [
        'Sample Testplan',
        'Primary',
        'AlphaSuite',
        'test_equality_passing2',
      ],
      ],
      [
        '/Sample%20Testplan/Primary/BetaSuite',
        [ 'Sample Testplan', 'Primary', 'BetaSuite' ],
      ],
      [
        '/Sample%20Testplan/Primary/BetaSuite/test_equality_passing', [
        'Sample Testplan',
        'Primary',
        'BetaSuite',
        'test_equality_passing',
      ],
      ],
      [ '/Sample%20Testplan/Secondary', [ 'Sample Testplan', 'Secondary' ] ],
      [
        '/Sample%20Testplan/Secondary/GammaSuite',
        [ 'Sample Testplan', 'Secondary', 'GammaSuite' ],
      ],
      [
        '/Sample%20Testplan/Secondary/GammaSuite/test_equality_passing',
        [
          'Sample Testplan',
          'Secondary',
          'GammaSuite',
          'test_equality_passing',
        ],
      ],
    ]));

  });

});
