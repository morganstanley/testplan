/**
 * Use this module to store utility functions / types that are *only* used in
 * tests. This helps prevent unnecessary bloating of the production bundle.
 *
 * To use one of these functions in production, move it to
 * {@link './../Common/utils.js'} and reexport it from here.
 */
import _ from 'lodash';
import uriComponentCodec
  from '../../Report/BatchReport_routing/utils/uriComponentCodec';

// `react-scripts test` sets NODE_ENV to "test". This module shouldn't be
// used at any other time. Thus we'll throw an error to ensure this.
if(process.env.NODE_ENV !== 'test') {
  throw new Error('This module is only to be used during testing');
}

/**
 * Generate random samples from an array.
 * @param {any[]} arr - The array to sample from
 * @param {number} [n=1] - The number of samples to take
 * @param {number} [minSz=1] - The minimum sample size to take from `arr`
 * @param {number} [maxSz=`arr.length`] - The max sample size to take from `arr`
 * @returns {Array<any[]>}
 */
export const randomSamples = (arr, n = 1, minSz = 1, maxSz = arr.length) =>
  Array.from({ length: n }, () => _.sampleSize(arr, _.random(minSz, maxSz)));

/**
 * Returns a new object with only `keepKeys`. If the corresponding value to one
 * of `keepKeys` is an object, that object is similarly filtered down to
 * only `keepKeys`. If the corresponding value to one of `keepKeys` is an
 * array,
 * an attempt is made to run the same filtering operation on each element.
 * @example
 * > const TESTPLAN_REPORT =
 *   require('../mocks/documents/TESTPLAN_REPORT_2.json');
 * > const TESTPLAN_REPORT_SLIM = filterObjectDeep(TESTPLAN_REPORT, ['name',
 *   'entries', 'category'])
 * > TESTPLAN_REPORT_SLIM
 * {
 *  name: "Sample Testplan",
 *  entries: [
 *    {
 *      name: "Primary",
 *      category: "multitest",
 *      entries: [
 *        {
 *          category: "testsuite",
 *          name: "AlphaSuite",
 *          entries: [
 *            {
 *              name: "test_equality_passing",
 *              category: "testcase",
 *              entries: [
 *                {
 *                  category: "DEFAULT"
 *                }
 *              ]
 *            },
 *            {
 *              name: "test_equality_passing2",
 *              category: "testcase",
 *              entries: [
 *                {
 *                  category: "DEFAULT"
 *                }
 *              ]
 *            }
 *          ]
 *        },
 *        {
 *          category: "testsuite",
 *          name: "BetaSuite",
 *          entries: [
 *            {
 *              name: "test_equality_passing",
 *              category: "testcase",
 *              entries: [
 *                {
 *                  category: "DEFAULT"
 *                }
 *              ]
 *            }
 *          ]
 *        }
 *      ]
 *    },
 *    {
 *      name: "Secondary",
 *      category: "multitest",
 *      entries: [
 *        {
 *          category: "testsuite",
 *          name: "GammaSuite",
 *          entries: [
 *            {
 *              name: "test_equality_passing",
 *              category: "testcase",
 *              entries: [
 *                {
 *                  category: "DEFAULT"
 *                }
 *              ]
 *            }
 *          ]
 *        }
 *      ]
 *    }
 *  ]
 * }
 *
 * @param {Object.<string, any>} obj - Object to filter
 * @param {string[]} keepKeys - Keys to keep from `obj`
 * @returns {Object.<string, any>} A copy of `obj` that contains only
 *   `keepKeys`
 */
export const filterObjectDeep = (obj, keepKeys) =>
  Object.fromEntries(Object.entries(obj)
    .filter(([prop]) => keepKeys.includes(prop))
    .map(([prop, val]) => [
      prop, (function handle(v) {
        return Array.isArray(v) ? v.map(_v => handle(_v)) :
          _.isObject(v) ? filterObjectDeep(v, keepKeys) : v;
      })(val)
    ])
  );

/**
 * Adapted from {@link https://stackoverflow.com/a/36128759|this SO answer} -
 * Returns an array of all possible paths for an object such that any element
 * can be used as the 2nd argument the {@link _.at} funtion.
 * @example
 * > // using TESTPLAN_REPORT_SLIM from the `filterObjectDeep` jsdoc example
 * > const TESTPLAN_REPORT_SLIM_PATH_STRINGS = getPaths(TESTPLAN_REPORT_SLIM);
 * > const TESTPLAN_REPORT_SLIM_PATH_ARRAYS = getPaths(TESTPLAN_REPORT_SLIM,
 *   true);
 * > TESTPLAN_REPORT_SLIM_PATH_STRINGS
 * [
 *   'name',
 *   'entries',
 *   'entries[0]',
 *   'entries[0].name',
 *   'entries[0].category',
 *   'entries[0].entries',
 *   'entries[0].entries[0]',
 *   'entries[0].entries[0].category',
 *   'entries[0].entries[0].name',
 *   'entries[0].entries[0].entries',
 *   'entries[0].entries[0].entries[0]',
 *   'entries[0].entries[0].entries[0].name',
 *   'entries[0].entries[0].entries[0].category',
 *   'entries[0].entries[0].entries[0].entries',
 *   'entries[0].entries[0].entries[0].entries[0]',
 *   'entries[0].entries[0].entries[0].entries[0].category',
 *   'entries[0].entries[0].entries[1]',
 *   'entries[0].entries[0].entries[1].name',
 *   'entries[0].entries[0].entries[1].category',
 *   'entries[0].entries[0].entries[1].entries',
 *   'entries[0].entries[0].entries[1].entries[0]',
 *   'entries[0].entries[0].entries[1].entries[0].category',
 *   'entries[0].entries[1]',
 *   'entries[0].entries[1].category',
 *   'entries[0].entries[1].name',
 *   'entries[0].entries[1].entries',
 *   'entries[0].entries[1].entries[0]',
 *   'entries[0].entries[1].entries[0].name',
 *   'entries[0].entries[1].entries[0].category',
 *   'entries[0].entries[1].entries[0].entries',
 *   'entries[0].entries[1].entries[0].entries[0]',
 *   'entries[0].entries[1].entries[0].entries[0].category',
 *   'entries[1]',
 *   'entries[1].name',
 *   'entries[1].category',
 *   'entries[1].entries',
 *   'entries[1].entries[0]',
 *   'entries[1].entries[0].category',
 *   'entries[1].entries[0].name',
 *   'entries[1].entries[0].entries',
 *   'entries[1].entries[0].entries[0]',
 *   'entries[1].entries[0].entries[0].name',
 *   'entries[1].entries[0].entries[0].category',
 *   'entries[1].entries[0].entries[0].entries',
 *   'entries[1].entries[0].entries[0].entries[0]',
 *   'entries[1].entries[0].entries[0].entries[0].category'
 * ]
 *
 * > TESTPLAN_REPORT_SLIM_PATH_ARRAYS
 *
 * [
 *   [ 'name' ],
 *   [ 'entries' ],
 *   [ 'entries', '0' ],
 *   [ 'entries', '0', 'name' ],
 *   [ 'entries', '0', 'category' ],
 *   [ 'entries', '0', 'entries' ],
 *   [ 'entries', '0', 'entries', '0' ],
 *   [ 'entries', '0', 'entries', '0', 'category' ],
 *   [ 'entries', '0', 'entries', '0', 'name' ],
 *   [ 'entries', '0', 'entries', '0', 'entries' ],
 *   [ 'entries', '0', 'entries', '0', 'entries', '0' ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'name',
 *   ],
 *   [ 'entries', '0', 'entries', '0', 'entries', '0', 'category' ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'category',
 *   ],
 *   [ 'entries', '0', 'entries', '0', 'entries', '1' ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '1',
 *     'name',
 *   ],
 *   [ 'entries', '0', 'entries', '0', 'entries', '1', 'category' ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '1',
 *     'entries',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *     'category',
 *   ],
 *   [ 'entries', '0', 'entries', '1' ],
 *   [ 'entries', '0', 'entries', '1', 'category' ],
 *   [ 'entries', '0', 'entries', '1', 'name' ],
 *   [ 'entries', '0', 'entries', '1', 'entries' ],
 *   [ 'entries', '0', 'entries', '1', 'entries', '0' ],
 *   [
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *     'name',
 *   ],
 *   [ 'entries', '0', 'entries', '1', 'entries', '0', 'category' ],
 *   [
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *     'entries',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *   ],
 *   [
 *     'entries', '0',
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *     'category',
 *   ],
 *   [ 'entries', '1' ],
 *   [ 'entries', '1', 'name' ],
 *   [ 'entries', '1', 'category' ],
 *   [ 'entries', '1', 'entries' ],
 *   [ 'entries', '1', 'entries', '0' ],
 *   [ 'entries', '1', 'entries', '0', 'category' ],
 *   [ 'entries', '1', 'entries', '0', 'name' ],
 *   [ 'entries', '1', 'entries', '0', 'entries' ],
 *   [ 'entries', '1', 'entries', '0', 'entries', '0' ],
 *   [
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *     'name',
 *   ],
 *   [ 'entries', '1', 'entries', '0', 'entries', '0', 'category' ],
 *   [
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries',
 *   ],
 *   [
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *   ],
 *   [
 *     'entries', '1',
 *     'entries', '0',
 *     'entries', '0',
 *     'entries', '0',
 *     'category',
 *   ],
 * ]
 *
 * @param {object} obj - A plain non-instance object
 * @param {boolean} [asArrays=false] - Pass `true` to return array-form paths
 * @returns {string[] | Array<string[]>}
 */
export const getPaths = (obj, asArrays = false) =>
  asArrays ? getPathArrays(obj) : getPathStrings(obj);

const getPathStrings = _.memoize(obj => {
  const pathStrings = [];
  (function walk(subObj, prevPathStr = '') {
    for(const [ prop, val ] of Object.entries(subObj)) {
      const propPathString = !prevPathStr ? prop : `${prevPathStr}.${prop}`;
      pathStrings.push(propPathString);
      if(_.isPlainObject(val)) {
        walk(val, propPathString);
      } else if(Array.isArray(val)) {
        val.forEach((v, i) => {
          const elementPathString = `${propPathString}[${i}]`;
          pathStrings.push(elementPathString);
          const elementVal = val[i];
          if(_.isPlainObject(elementVal)) {
            walk(elementVal, elementPathString);
          }
        });
      }
    }
  })(obj);
  return pathStrings;
});

const getPathArrays = _.memoize(
  obj => getPathStrings(obj).map(v => _.toPath(v))
);

/**
 * Reverses a `Map`.
 * @param {Map} aMap
 * @returns {Map}
 */
export function reverseMap(aMap) {
  const revMap = new Map();
  for(const [prop, val] of aMap) {
    revMap.set(val, prop);
  }
  return revMap;
}

/**
 * Get the URL paths that could be traversed in a given report
 * @example
 > const aliasMap = new Map();
 > const path2PathArrayMap = new Map();
 > const expectedPaths = deriveURLPathsFromReport(TESTPLAN_REPORT_1, aliasMap, path2PathArrayMap);
 > expectedPaths
 [
 '/Sample Testplan',
 '/Sample Testplan/Primary',
 '/Sample Testplan/Primary/AlphaSuite',
 '/Sample Testplan/Primary/AlphaSuite/test_equality_passing',
 '/Sample Testplan/Primary/AlphaSuite/test_equality_passing2',
 '/Sample Testplan/Primary/BetaSuite',
 '/Sample Testplan/Primary/BetaSuite/test_equality_passing',
 '/Sample Testplan/Secondary',
 '/Sample Testplan/Secondary/GammaSuite',
 '/Sample Testplan/Secondary/GammaSuite/test_equality_passing'
 ]
 > aliasMap
 Map {
  'Sample Testplan' => 'Sample Testplan',
  'Primary' => 'Primary',
  'AlphaSuite' => 'AlphaSuite',
  'test_equality_passing' => 'test_equality_passing',
  'test_equality_passing2' => 'test_equality_passing2',
  'BetaSuite' => 'BetaSuite',
  'Secondary' => 'Secondary',
  'GammaSuite' => 'GammaSuite'
}
 > path2PathArrayMap
 Map {
  '/Sample Testplan' => [ 'Sample Testplan' ],
  '/Sample Testplan/Primary' => [ 'Sample Testplan', 'Primary' ],
  '/Sample Testplan/Primary/AlphaSuite' => [ 'Sample Testplan', 'Primary', 'AlphaSuite' ],
  '/Sample Testplan/Primary/AlphaSuite/test_equality_passing' => [
    'Sample Testplan',
    'Primary',
    'AlphaSuite',
    'test_equality_passing'
  ],
  '/Sample Testplan/Primary/AlphaSuite/test_equality_passing2' => [
    'Sample Testplan',
    'Primary',
    'AlphaSuite',
    'test_equality_passing2'
  ],
  '/Sample Testplan/Primary/BetaSuite' => [ 'Sample Testplan', 'Primary', 'BetaSuite' ],
  '/Sample Testplan/Primary/BetaSuite/test_equality_passing' => [
    'Sample Testplan',
    'Primary',
    'BetaSuite',
    'test_equality_passing'
  ],
  '/Sample Testplan/Secondary' => [ 'Sample Testplan', 'Secondary' ],
  '/Sample Testplan/Secondary/GammaSuite' => [ 'Sample Testplan', 'Secondary', 'GammaSuite' ],
  '/Sample Testplan/Secondary/GammaSuite/test_equality_passing' => [
    'Sample Testplan',
    'Secondary',
    'GammaSuite',
    'test_equality_passing'
  ]
}
 * @param {object} report
 * @param {null | Map<string, string>} [aliasMap=null]
 * @param {null | Map<string, string[]>} [path2PathArrayMap=null]
 * @param {null | Map<string, string[]>} [path2ObjectPathMap=null]
 * @returns {string[]}
 */
export function deriveURLPathsFromReport(
  report,
  aliasMap = null,
  path2PathArrayMap = null,
  path2ObjectPathMap = null,
) {
  const pathMap = new Map();
  return getPaths(report, true)
    // @ts-ignore
    .filter(arrayPath => arrayPath.slice(-1)[0] === 'name')
    .map(arrayPath => {
      const
        fullPathKey = arrayPath.slice(0, -1).join('.'),
        pathBasename = _.get(report, arrayPath),
        pathBasenameEncoded = uriComponentCodec.encode(pathBasename),
        parentPathKey = arrayPath.slice(0, -3).join('.'),
        parentPath = pathMap.get(parentPathKey) || '',
        fullPathVal = `${parentPath}/${pathBasenameEncoded}`;
      pathMap.set(fullPathKey, fullPathVal);
      if(aliasMap !== null) {
        aliasMap.set(pathBasenameEncoded, pathBasename);
      }
      if(path2PathArrayMap !== null) {
        const parentPathArr = path2PathArrayMap.get(parentPath) || [];
        path2PathArrayMap.set(fullPathVal, parentPathArr.concat(pathBasename));
      }
      if(path2ObjectPathMap !== null) {
        path2ObjectPathMap.set(fullPathVal, arrayPath);
      }
      return fullPathVal;
    });
}

/**
 * Like {@link https://lodash.com/docs/4.17.15#matches|this} but recursively.
 * @example
 > const obj = {
     a: 11,
     b: 2,
     c: {
       a: 1,
       x: 'a',
     },
     d: [
       { a: 1, b: 22 },
       { a: 11, c: 33 },
       { a: 111, d: [ { a: 1, y: 'aa' } ]}
     ]
   }
 > findAllDeep(obj, { a: 1 }, [ 'c', 'd' ])
 [
 { "a": 1, "x": "a" },
 { "a": 1, "b": 22 },
 { "a": 1, "y": "aa" },
 ]
 > findAllDeep(obj, { a: 1 }, 'c')
 [ { "a": 1, "x": "a" } ]

 * @param {Object.<string, any>} srcObj - object to run the find on
 * @param {Object.<string, string | number | boolean | bigint | symbol>} matchObj - partial object to match against
 * @param {null | string[]} [diveProps=null] - properties that will be searched recursively for matches
 * @returns {object[]} array of all found objects
 */
export const findAllDeep = (srcObj, matchObj, diveProps = null) =>
  [ _.find([ srcObj ], matchObj) ].concat(
    [ diveProps ].flat().filter(Boolean).flatMap(
      prop =>
        srcObj[prop]
          ? Array.isArray(srcObj[prop])
          ? srcObj[prop].flatMap(el => findAllDeep(el, matchObj, prop))
          : _.isPlainObject(srcObj[prop])
            ? [ _.find([ srcObj[prop] ], matchObj) ]
            : []
          : [],
    ),
  ).filter(Boolean);
