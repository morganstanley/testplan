import * as filterStates from './filterStates';
import _isPlainObject from 'lodash/isPlainObject';
import _isEqual from 'lodash/isEqual';
import _assignWith from 'lodash/assignWith';
import _at from 'lodash/at';
import { MAX_SIGNED_31_BIT_INT, queryStringToMap } from '../../../Common/utils';
export { default as uriComponentCodec } from './uriComponentCodec';

/**
 * @typedef MapOrObjectToFunc
 * @type {Map<string, Function> | Object.<string, Function> | {}}
 */
/** @typedef {any |string |number |boolean |null |symbol |BigInt} ActuallyAny */
/** @typedef {typeof import("../state/actionTypes")} ActionTypes */
/** @typedef {typeof import("../state/actionChangeTypes")} ActionChangeTypes */
/**
 * @template P
 * @typedef AppAction<P>
 * @property {ActionTypes[keyof ActionTypes]} type
 * @property {ActionChangeTypes[keyof ActionChangeTypes]} change
 * @property {P} payload
 * @property {null | function(Object.<string, any>): void} callback
 */

export const safeGetNumPassedFailedErrored = (counter,
  coalesceVal = null) => counter ?
  [
    counter.passed || coalesceVal,
    counter.failed || coalesceVal,
    counter.error || coalesceVal,
  ] : [ coalesceVal, coalesceVal, coalesceVal ];

export const isFilteredOut =
  (filter, [ numPassed = 0, numFailed = 0, numErrored = 0 ]) =>
    (filter === filterStates.PASSED && numPassed === 0) ||
    (filter === filterStates.FAILED && (numFailed + numErrored) === 0);

export const getChangedBitsCalculator = (maskMap) =>
  (prev, curr) => Object.entries(maskMap).reduce(
    (mask, [ prop, bytes ]) => mask | (
      _isPlainObject(bytes)
        ? getChangedBitsCalculator(bytes)(prev[prop], curr[prop])
        : _isEqual(prev[prop], curr[prop])
        ? 0
        : bytes
    ), 0);

export function makeMaskMap(templateObj) {
  let i = 0;
  return _assignWith({}, templateObj, function _inner(_ignored, v) {
    return _isPlainObject(v) ? _assignWith({}, v, _inner) : (1 << (i++));
  });
}

export const getObservedBitsGetter = bitmaskMap => objectPath =>
  objectPath === false
    ? 0
    : objectPath === undefined
    ? MAX_SIGNED_31_BIT_INT
    : _at(bitmaskMap, objectPath).reduce(
      function _inner(prev, curr) {
        return prev | (
          _isPlainObject(curr) ? Object.values(curr).reduce(_inner, 0) : curr
        );
      }, 0);

/**
 * This is meant to be used by functions that dispatch mapped actions based on
 * the window's URI query params. It safely generates the actions indicated
 * by the window's query params.
 * @param {(Map<string, ActuallyAny> | string)} queryStringOrMap
 * @param {function(Map<string, ActuallyAny>): AppAction<any>} saveFullUriQueryFunc
 * @param {MapOrObjectToFunc} queryParamsActionCreatorsMapOrObj
 */
export function deriveActionsFromUriQueryParams(
  queryStringOrMap,
  saveFullUriQueryFunc,
  queryParamsActionCreatorsMapOrObj,
) {
  const queryMap = queryStringOrMap instanceof Map
    ? queryStringOrMap
    : queryStringToMap(queryStringOrMap);
  const queryActionMapping = queryParamsActionCreatorsMapOrObj instanceof Map
    ? queryParamsActionCreatorsMapOrObj
    : new Map(Object.entries(queryParamsActionCreatorsMapOrObj));
  const actions = [ saveFullUriQueryFunc(queryMap) ];
  for(const [ param, val ] of queryMap) {
    const tgtActionCreator = queryActionMapping.get(param);
    if(typeof tgtActionCreator === 'function') {
      actions.push(tgtActionCreator(val));
    } else {
      console.warn(`Unused query parameter "${param}".`);
    }
  }
  return actions;
}
