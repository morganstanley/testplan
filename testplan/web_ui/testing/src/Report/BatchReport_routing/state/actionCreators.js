import * as actionTypes from './actionTypes';
import * as actionChangeTypes from './actionChangeTypes';
import {
  hashQueryActionCreatorMap, queryActionCreatorMap,
} from './uriQueryActions';
import { deriveActionsFromUriQueryParams } from '../utils';

/** @typedef {(any|string|number|boolean|null|symbol|BigInt)} ActuallyAny */
/** @typedef {typeof actionTypes} ActionTypes */
/** @typedef {typeof actionChangeTypes} ActionChangeTypes */
/** @typedef {typeof import("../utils/filterStates")} FilterStates */
/** @typedef {typeof import("./actionCreators")} ThisModule */
/**
 * @template P
 * @typedef AppAction<P>
 * @property {ActionTypes[keyof ActionTypes]} type
 * @property {ActionChangeTypes[keyof ActionChangeTypes]} change
 * @property {P} payload
 * @property {null | function(Object.<string, any>): void} callback
 */

/**
 * For more info on action creators see the
 * {@link https://redux.js.org/basics/actions#action-creators Redux docs}
 */
const actionCreators = {
  /**
   * @param {boolean} isTesting
   * @returns {AppAction<{isTesting: boolean}>}
   */
  setIsTesting: (isTesting) => {
    const NODE_ENV = process.env.NODE_ENV,
      CI = process.env.CI,
      acceptableNodeEnvVals = [ 'development', 'test' ],
      // @ts-ignore
      testingAllowed = acceptableNodeEnvVals.includes(NODE_ENV) ||
                       typeof CI !== 'undefined',
      screenedIsTesting = isTesting && testingAllowed;
    return {
      type: actionTypes.IS_TESTING,
      change: actionChangeTypes.REPLACE,
      payload: { isTesting: screenedIsTesting },
      callback: !isTesting || (isTesting === testingAllowed) ? null : () => {
        console.warn(
          `Cannot enter testing mode since NODE_ENV="${NODE_ENV}"` +
          ` and CI="${CI}". Set the environment variable CI to anything, or` +
          ` NODE_ENV to any of "${acceptableNodeEnvVals.join('" / "')}",` +
          ` and rebuild.`
        );
      },
    };
  },

  /**
   * @param {boolean} doAutoSelect
   * @returns {AppAction<{doAutoSelect: boolean}>}
   */
  setAppBatchReportDoAutoSelect: (doAutoSelect) => ({
    type: actionTypes.APP_BATCHREPORT_DO_AUTO_SELECT,
    change: actionChangeTypes.REPLACE,
    payload: { doAutoSelect },
    callback: null,
  }),

  /**
   * @param {null | Object.<string, ActuallyAny>} selectedTestCase
   * @returns {AppAction<{selectedTestCase: null|Object.<string, ActuallyAny>}>}
   */
  setAppBatchReportSelectedTestCase: (selectedTestCase) => ({
    type: actionTypes.APP_BATCHREPORT_SELECTED_TEST_CASE,
    change: actionChangeTypes.REPLACE,
    payload: { selectedTestCase },
    callback: null,
  }),

  /**
   * @param {string} component - the name of the path component
   * @param {string} alias - another name for the path component
   * @returns {AppAction<{alias: string, component: string}>}
   */
  setUriHashPathComponentAlias: (alias, component) => ({
    type: actionTypes.URI_HASH_ALIASES,
    change: actionChangeTypes.REPLACE,
    payload: { alias, component },
    callback: null,
  }),

  /**
   * Adds ability to set state from a URI query params
   * @param {Map<string, ActuallyAny>} queryMap
   * @returns {AppAction<Object.<"mapping", Map<string, ActuallyAny>>>}
   */
  saveUriHashQuery: (queryMap) => ({
    type: actionTypes.URI_HASH_QUERY,
    change: actionChangeTypes.REPLACE,
    payload: { mapping: queryMap },
    callback: null,
  }),

  /**
   * Adds ability to set state from a URI query params
   * @param {Map<string, ActuallyAny>} queryMap
   * @returns {AppAction<Object.<"mapping", Map<string, ActuallyAny>>>}
   */
  saveUriQuery: (queryMap) => ({
    type: actionTypes.URI_QUERY,
    change: actionChangeTypes.REPLACE,
    payload: { mapping: queryMap },
    callback: null,
  }),

  /**
   * @param {boolean} isDisplayEmpty
   * @returns {AppAction<{isDisplayEmpty: boolean}>}
   */
  setAppBatchReportIsDisplayEmpty: (isDisplayEmpty) => ({
    type: actionTypes.APP_BATCHREPORT_DISPLAY_EMPTY,
    change: actionChangeTypes.REPLACE,
    payload: { isDisplayEmpty },
    callback: null,
  }),

  /**
   * @param {FilterStates[keyof FilterStates]} filter
   * @returns {AppAction<{filter: FilterStates[keyof FilterStates]}>}
   */
  setAppBatchReportFilter: (filter) => ({
    type: actionTypes.APP_BATCHREPORT_FILTER,
    change: actionChangeTypes.REPLACE,
    payload: { filter },
    callback: null,
  }),

  /**
   * @param {boolean} isFetching
   * @returns {AppAction<{isFetching: boolean}>}
   */
  setAppBatchReportIsFetching: (isFetching) => ({
    type: actionTypes.APP_BATCHREPORT_FETCHING,
    change: actionChangeTypes.REPLACE,
    payload: { isFetching },
    callback: null,
  }),

  /**
   * @param {boolean} isLoading
   * @returns {AppAction<{isLoading: boolean}>}
   */
  setAppBatchReportIsLoading: (isLoading) => ({
    type: actionTypes.APP_BATCHREPORT_LOADING,
    change: actionChangeTypes.REPLACE,
    payload: { isLoading },
    callback: null,
  }),

  /**
   * @param {Error | null} fetchError
   * @returns {AppAction<{fetchError: Error | null}>}
   */
  setAppBatchReportFetchError: (fetchError) => ({
    type: actionTypes.APP_BATCHREPORT_FETCH_ERROR,
    change: actionChangeTypes.REPLACE,
    payload: { fetchError },
    callback: null,
  }),

  /**
   * @param {boolean} isShowTags
   * @returns {AppAction<{isShowTags: boolean}>}
   */
  setAppBatchReportIsShowTags: (isShowTags) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_TAGS,
    change: actionChangeTypes.REPLACE,
    payload: { isShowTags },
    callback: null,
  }),

  /**
   * @param {object} jsonReport
   * @returns {AppAction<{jsonReport: object}>}
   */
  setAppBatchReportJsonReport: (jsonReport) => ({
    type: actionTypes.APP_BATCHREPORT_JSON_REPORT,
    change: actionChangeTypes.REPLACE,
    payload: { jsonReport },
    callback: null,
  }),

  /**
   * @param {boolean} isShowHelpModal
   * @returns {AppAction<{isShowHelpModal: boolean}>}
   */
  setAppBatchReportShowHelpModal: (isShowHelpModal) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_HELP_MODAL,
    change: actionChangeTypes.REPLACE,
    payload: { isShowHelpModal },
    callback: null,
  }),

  /**
   * @param {boolean} isShowInfoModal
   * @returns {AppAction<{isShowInfoModal: boolean}>}
   */
  setAppBatchReportShowInfoModal: (isShowInfoModal) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_INFO_MODAL,
    change: actionChangeTypes.REPLACE,
    payload: { isShowInfoModal },
    callback: null,
  }),

  /**
   * @param {(Map<string, ActuallyAny> | string)} query
   * @returns {Array<ReturnType<Omit<ThisModule[keyof ThisModule], 'mapUriHashQueryToState'>>>}
   */
  mapUriHashQueryToState: (query) =>
    deriveActionsFromUriQueryParams(
      query,
      actionCreators.saveUriHashQuery,
      hashQueryActionCreatorMap()
    ),

  /**
   * @param {(Map<string, ActuallyAny> | string)} query
   * @returns {Array<ReturnType<Omit<ThisModule[keyof ThisModule], 'mapUriQueryToState'>>>}
   */
  mapUriQueryToState: (query) =>
    deriveActionsFromUriQueryParams(
      query,
      actionCreators.saveUriQuery,
      queryActionCreatorMap()
    ),
};

export default actionCreators;
