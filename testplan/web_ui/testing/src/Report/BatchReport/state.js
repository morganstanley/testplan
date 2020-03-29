import React, {
  createContext, useReducer, useContext, useMemo, useRef
} from 'react';
import _at from 'lodash/at';
import _isEqual from 'lodash/isEqual';
import produce from 'immer';
import { queryStringToMap, mapToQueryString } from '../../Common/utils';
import { uiHistory } from './UIRouter';

/**
 * @typedef FilterStates
 * @property {"all"} ALL
 * @property {"fail"} FAILED
 * @property {"pass"} PASSED
 * @readonly
 */
/** @typedef {(any|string|number|boolean|null|symbol|BigInt)} ActuallyAny */
/**
 * @template P
 * @typedef AppAction<P>
 * @property {string} type
 * @property {string} change
 * @property {P} payload
 * @property {null | function(Object.<string, any>): void} callback
 */
/** @typedef {typeof actionCreators} AppActionCreatorsObj */
/**
 * @typedef {AppActionCreatorsObj[keyof AppActionCreatorsObj]} AppActionCreators
 */
/** @typedef {typeof queryParamActionCreatorMap} QueryParamActionCreators */

export const filterStates = {
  /** @const */ ALL: 'all',
  /** @const */ FAILED: 'fail',
  /** @const */ PASSED: 'pass',
};

/// State
export const defaultState = {
  documentation: {
    url: {
      external: 'http://testplan.readthedocs.io',
      internal: 'http://testplan.readthedocs.io',
    },
  },
  uri: {
    hash: {
      /** @type {Map<string, string>} */
      aliases: new Map(),
      /** @type {Map<string, string>} */
      query: new Map(),
    },
  },
  app: {
    reports: {
      batch: {
        /** @type {boolean} */
        isShowHelpModal: false,
        /** @type {boolean} */
        isDisplayEmpty: true,
        /* @type {FilterStates[keyof FilterStates]} */
        filter: filterStates.ALL,
        /** @type {boolean} */
        isFetching: false,
        /** @type {boolean} */
        isLoading: false,
        /** @type {null | Error} */
        fetchError: null,
        /** @type {boolean} */
        isShowTags: false,
        /** @type {null | Object.<string, any>} */
        jsonReport: null,
        /** @type {boolean} */
        isShowInfoModal: false,
        /** @type {null | Object.<string, ActuallyAny>} */
        selectedTestCase: null,
        /** @type {boolean} */
        doAutoSelect: true,
      },
      interactive: null,
    },
  },
};

// Action types
export const actionTypes = {
  URI_HASH_ALIASES: 'uri/hash/aliases',
  URI_HASH_QUERY: 'uri/hash/query',
  APP_BATCHREPORT_DO_AUTO_SELECT: 'app/reports/batch/doAutoSelect',
  APP_BATCHREPORT_DISPLAY_EMPTY: 'app/reports/batch/isDisplayEmpty',
  APP_BATCHREPORT_FILTER: 'app/reports/batch/filter',
  APP_BATCHREPORT_FETCHING: 'app/reports/batch/isFetching',
  APP_BATCHREPORT_LOADING: 'app/reports/batch/isLoading',
  APP_BATCHREPORT_FETCH_ERROR: 'app/reports/batch/fetchError',
  APP_BATCHREPORT_SHOW_TAGS: 'app/reports/batch/isShowTags',
  APP_BATCHREPORT_JSON_REPORT: 'app/reports/batch/jsonReport',
  APP_BATCHREPORT_SHOW_HELP_MODAL: 'app/reports/batch/isShowHelpModal',
  APP_BATCHREPORT_SHOW_INFO_MODAL: 'app/reports/batch/isShowInfoModal',
  APP_BATCHREPORT_SELECTED_TEST_CASE: 'app/reports/batch/selectedTestCase',
};

// Action subtypes
export const changeTypes = {
  REPLACE: 'REPLACE',
  DELETE: 'DELETE',
  PATCH: 'PATCH',
};

function devLog(prefix) {
  const prefixVal = typeof prefix === 'function' ? prefix() : prefix;
  if(process.env.NODE_ENV === 'development')
    return (msg) => {
      const msgVal = typeof msg === 'function' ? msg() : msg;
      console.debug(
        prefixVal,
        JSON.stringify(
          msgVal === undefined ? '' : msgVal,
          (key, val) => typeof val === 'function' ? val.toString() : val,
          2,
          )
      );
    };
  return () => undefined;
}

/// Reducer
/* eslint-disable default-case */
/**
 * {
 *   type: ...,
 *   change: ...,
 *   payload: ...,
 *   callback: ...,
 * }
 *
 * */
export const appReducer = produce((draftState, action) => {
  // default case not needed: immerjs.github.io/immer/docs/example-reducer
  devLog('appReducer action:')(action);

  switch(action.type) {

    case actionTypes.APP_BATCHREPORT_DO_AUTO_SELECT:
      switch(action.change) {

        case changeTypes.REPLACE:
        case changeTypes.PATCH:
          const { doAutoSelect } = action.payload;
          draftState.app.reports.batch.doAutoSelect = doAutoSelect;
          break;
      }
      break;

    case actionTypes.URI_HASH_ALIASES:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { alias, component } = action.payload;
          draftState.uri.hash.aliases.set(alias, component);
          break;
      }
      break;

    case actionTypes.URI_HASH_QUERY:
      switch(action.change) {

        case changeTypes.REPLACE:
          draftState.uri.hash.query.clear();
        // eslint-disable-next-line no-fallthrough
        case changeTypes.PATCH:
          for(const [param, val] of action.payload.mapping) {
            draftState.uri.hash.query.set(param, val);
          }
          break;

        case changeTypes.DELETE:
          for(const param of action.payload.values) {
            draftState.uri.hash.query.delete(param);
          }
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_DISPLAY_EMPTY:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isDisplayEmpty } = action.payload;
          draftState.app.reports.batch.isDisplayEmpty = isDisplayEmpty;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_FILTER:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { filter } = action.payload;
          draftState.app.reports.batch.filter = filter;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_FETCHING:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isFetching } = action.payload;
          draftState.app.reports.batch.isFetching = isFetching;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_LOADING:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isLoading } = action.payload;
          draftState.app.reports.batch.isLoading = isLoading;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_FETCH_ERROR:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { fetchError } = action.payload;
          draftState.app.reports.batch.fetchError = fetchError;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_SHOW_TAGS:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isShowTags } = action.payload;
          draftState.app.reports.batch.isShowTags = isShowTags;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_JSON_REPORT:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { jsonReport } = action.payload;
          draftState.app.reports.batch.jsonReport = jsonReport;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_SHOW_HELP_MODAL:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isShowHelpModal } = action.payload;
          draftState.app.reports.batch.isShowHelpModal = isShowHelpModal;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_SHOW_INFO_MODAL:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { isShowInfoModal } = action.payload;
          draftState.app.reports.batch.isShowInfoModal = isShowInfoModal;
          break;
      }
      break;

    case actionTypes.APP_BATCHREPORT_SELECTED_TEST_CASE:
      switch(action.change) {

        case changeTypes.PATCH:
        case changeTypes.REPLACE:
          const { selectedTestCase } = action.payload;
          draftState.app.reports.batch.selectedTestCase = selectedTestCase;
          break;
      }
      break;
  }

  if(typeof action.callback === 'function') {
    action.callback(draftState);
  }
});
/* eslint-enable default-case */

/// Action creators
export const actionCreators = {
  /**
   * @param {boolean} doAutoSelect
   * @returns {AppAction<{doAutoSelect: boolean}>}
   */
  setAppBatchReportDoAutoSelect: (doAutoSelect) => ({
    type: actionTypes.APP_BATCHREPORT_DO_AUTO_SELECT,
    change: changeTypes.REPLACE,
    payload: { doAutoSelect },
    callback: null,
  }),
  /**
   * @param {null | Object.<string, ActuallyAny>} selectedTestCase
   * @returns {AppAction<{selectedTestCase: null|Object.<string, ActuallyAny>}>}
   */
  setAppBatchReportSelectedTestCase: (selectedTestCase) => ({
    type: actionTypes.APP_BATCHREPORT_SELECTED_TEST_CASE,
    change: changeTypes.REPLACE,
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
    change: changeTypes.REPLACE,
    payload: { alias, component },
    callback: null,
  }),
  /**
   * @param {string} param
   * @param {ActuallyAny} val
   * @returns {AppAction<{mapping: Map<string, ActuallyAny>}>}
   */
  setUriHashQueryParam: (param, val) => ({
    type: actionTypes.URI_HASH_QUERY,
    change: changeTypes.PATCH,
    payload: { mapping: new Map([[ param, val ]]) },
    callback: null,
  }),
  /**
   * @param {string | string[]} params
   * @returns {AppAction<{values: string | string[]}>}
   */
  deleteUriHashQueryParams: (params) => ({
    type: actionTypes.URI_HASH_QUERY,
    change: changeTypes.DELETE,
    payload: { values: Array.isArray(params) ? params : [ params ] },
    callback: null,
  }),
  /**
   * @param {boolean} isDisplayEmpty
   * @returns {AppAction<{isDisplayEmpty: boolean}>}
   */
  setAppBatchReportIsDisplayEmpty: (isDisplayEmpty) => ({
    type: actionTypes.APP_BATCHREPORT_DISPLAY_EMPTY,
    change: changeTypes.REPLACE,
    payload: { isDisplayEmpty },
    callback: null,
  }),
  /**
   * @param {FilterStates[keyof FilterStates]} filter
   * @returns {AppAction<{filter: FilterStates[keyof FilterStates]}>}
   */
  setAppBatchReportFilter: (filter) => ({
    type: actionTypes.APP_BATCHREPORT_FILTER,
    change: changeTypes.REPLACE,
    payload: { filter },
    callback: null,
  }),
  /**
   * @param {boolean} isFetching
   * @returns {AppAction<{isFetching: boolean}>}
   */
  setAppBatchReportIsFetching: (isFetching) => ({
    type: actionTypes.APP_BATCHREPORT_FETCHING,
    change: changeTypes.REPLACE,
    payload: { isFetching },
    callback: null,
  }),
  /**
   * @param {boolean} isLoading
   * @returns {AppAction<{isLoading: boolean}>}
   */
  setAppBatchReportIsLoading: (isLoading) => ({
    type: actionTypes.APP_BATCHREPORT_LOADING,
    change: changeTypes.REPLACE,
    payload: { isLoading },
    callback: null,
  }),
  /**
   * @param {Error} fetchError
   * @returns {AppAction<{fetchError: Error}>}
   */
  setAppBatchReportFetchError: (fetchError) => ({
    type: actionTypes.APP_BATCHREPORT_FETCH_ERROR,
    change: changeTypes.REPLACE,
    payload: { fetchError },
    callback: null,
  }),
  /**
   * @param {boolean} isShowTags
   * @returns {AppAction<{isShowTags: boolean}>}
   */
  setAppBatchReportIsShowTags: (isShowTags) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_TAGS,
    change: changeTypes.REPLACE,
    payload: { isShowTags },
    callback: null,
  }),
  /**
   * @param {object} jsonReport
   * @returns {AppAction<{jsonReport: object}>}
   */
  setAppBatchReportJsonReport: (jsonReport) => ({
    type: actionTypes.APP_BATCHREPORT_JSON_REPORT,
    change: changeTypes.REPLACE,
    payload: { jsonReport },
    callback: null,
  }),
  /**
   * @param {boolean} isShowHelpModal
   * @returns {AppAction<{isShowHelpModal: boolean}>}
   */
  setAppBatchReportShowHelpModal: (isShowHelpModal) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_HELP_MODAL,
    change: changeTypes.REPLACE,
    payload: { isShowHelpModal },
    callback: null,
  }),
  /**
   * @param {boolean} isShowInfoModal
   * @returns {AppAction<{isShowInfoModal: boolean}>}
   */
  setAppBatchReportShowInfoModal: (isShowInfoModal) => ({
    type: actionTypes.APP_BATCHREPORT_SHOW_INFO_MODAL,
    change: changeTypes.REPLACE,
    payload: { isShowInfoModal },
    callback: null,
  }),
  /**
   * Adds ability to set state from a URI query params
   * @param {Map<string, ActuallyAny>} queryMap
   * @returns {AppAction<Object.<"mapping", Map<string, ActuallyAny>>>}
   */
  saveUriHashQuery: (queryMap) => ({
    type: actionTypes.URI_HASH_QUERY,
    change: changeTypes.REPLACE,
    payload: { mapping: queryMap },
    callback: null,
  }),
  /**
   * @param {(Map<string, ActuallyAny> | string)} query
   * @returns {Array<
   *   ReturnType<QueryParamActionCreators[keyof QueryParamActionCreators]>
   * >}
   */
  mapUriHashQueryToState(query) {
    const queryMap = query instanceof Map ? query : queryStringToMap(query);
    const actions = [ actionCreators.saveUriHashQuery(queryMap) ];
    for(const [ param, val ] of queryMap) {
      const tgtActionCreator = queryParamActionCreatorMap[param];
      if(typeof tgtActionCreator === 'function') {
        actions.push(tgtActionCreator(val));
      } else {
        console.warn(`Unused query parameter "${param}".`);
      }
    }
    return actions;
  },
};

/**
 * <p>
 * This object maps URl query parameters with action creators. The keys should
 * be URL query params and the values should be values from
 * {@link actionCreators}.
 * </p><p/>
 * This object is used like so:
 * <ol><li>
 *   A query param (key) is manually set in the URL =>
 *   the mapped action creator (value) is dispatched
 * </li><li>
 *   One of the mapped action creators (values) is dispatched =>
 *   the associated query param (key) is set in the URL
 * </li></ol>
 * <p>
 * <b>IMPORTANT1</b>: This must be maintained as a 1-1 mapping, i.e. it should
 *                    be a valid js object of the same length if the values were
 *                    swapped with the keys.
 * </p>
 * <p>
 * <b>IMPORTANT2</b>: The action creators must take a single argument and return
 *                    a single action (not an array.of actions).
 * </p>
 * @type {Object.<string, AppActionCreators>}
 */
const queryParamActionCreatorMap = {
  displayEmpty: actionCreators.setAppBatchReportIsDisplayEmpty,
  filter: actionCreators.setAppBatchReportFilter,
  showTags: actionCreators.setAppBatchReportIsShowTags,
  doAutoSelect: actionCreators.setAppBatchReportDoAutoSelect,
};

/**
 * This function adds hooks to {@link actionCreators} such that whenever one is
 * the 'to' value in {@link queryParamActionCreatorMap} is used then the
 * corresponding 'from' value is set in the URL.
 */
function addQueryParamHooksToActionCreators() {
  const actionCreatorQueryParamMap = new Map(
    Object.entries(queryParamActionCreatorMap).map(
      ([queryParam, func]) => [func, queryParam]
    )
  );
  return Object.fromEntries(
    Object.entries(actionCreators).map(([name, func]) => {
      // `Map.get` essentially uses `Object.is` to match keys, see
      // http://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Map#Key_equality
      const queryParam = actionCreatorQueryParamMap.get(func);
      if(!queryParam) return [name, func];
      return [name, (val) => {
        const unhookedAction = func(val);
        const origCallback = unhookedAction.callback;
        return {
          ...unhookedAction,
          callback: draftState => {
            if(typeof origCallback === 'function') origCallback(draftState);
            draftState.uri.hash.query.set(queryParam, val);
            // // const currQueryMap = new Map(_at(draftState, 'uri.hash.query')[0]);
            // // this value is cycled back to 'uri.hash.query' via the history
            // // listener in `BatchReportStartup`.
            // currQueryMap.set(queryParam, val);
            uiHistory.push({
              ...uiHistory.location,
              search: mapToQueryString(draftState.uri.hash.query)
            });
          }
        };
      }];
    })
  );
}

/// Bound Action Creator
/**
 * <p>
 * This binds our action creators to the passed dispatch function so our actions
 * are automatically dispatched when calling one of the returned functions.
 * </p>
 * <p>
 * This function also adds hooks for the action creators mapped in
 * {@link queryParamActionCreatorMap} so that when one of the mapped action
 * creators is called then the associated query param is automatically appended
 * to the window's URL, i.e. it implements item (2) from that object's jsdoc.
 * </p>
 * @callback {React.Dispatch<ReturnType<AppActionCreatorsObj>>} dispatchFunc
 * @returns {Record<
 *   keyof AppActionCreatorsObj,
 *   function(Parameters<AppActionCreators>): void
 * > & React.Dispatch<ReturnType<AppActionCreators>>}
 */
const createAppDispatch = dispatchFunc => { //uiHistory
  // the raw dispatch func is also made available on the returned object
  const hookedActionCreators = addQueryParamHooksToActionCreators();
  const boundActionCreators = { dispatch: dispatchFunc };
  for(const [name, func] of Object.entries(hookedActionCreators)) {
    const wrappedFunc = (...args) => {
      const actions = func(...args);
      const actionsArr = Array.isArray(actions) ? actions : [ actions ];
      for(const action of actionsArr) {
        dispatchFunc(action);
      }
    };
    Object.defineProperty(wrappedFunc, "length", { value: func.length });
    Object.defineProperty(wrappedFunc, "name", { value: func.name });
    boundActionCreators[name] = wrappedFunc;
  }
  return boundActionCreators;
};

/// Context
/**
 * This is returned from `useContext(AppContext)` when we're in a component
 * that's not a child of `AppContext.Provider`.
 * @see https://reactjs.org/docs/context.html#reactcreatecontext
 */
const NOT_CHILD_OF_APP_CONTEXT_PROVIDER = 'NOT_CHILD_OF_APP_CONTEXT_PROVIDER';

/**
 * @typedef {(
 *   React.Context<(
 *     { 0: typeof defaultState, 1: ReturnType<typeof createAppDispatch> }
 *   )>
 * )} AppContext
 * @default
 */
export const AppContext = createContext(NOT_CHILD_OF_APP_CONTEXT_PROVIDER);

/**
 * @see https://reactjs.org/docs/context.html#contextdisplayname
 *  This is displayed in error messages and React DevTools
 **/
AppContext.displayName =
  ' /* global state store ==> */' +
  ' AppContext' +
  ' /* ==> access from a child of `AppStateProvider` with `useAppState` */';

// Provider component
/**
 * Makes children eligible for using the `useAppState` hook
 * @type {React.FunctionComponent<React.PropsWithChildren<any>>}
 */
export function AppStateProvider({ children, ...props }) {
  const [ state, unboundDispatch ] = useReducer(appReducer, defaultState);
  const boundActions = createAppDispatch(unboundDispatch);
  const appNetwork = [ state, boundActions ];
  return (
    // @ts-ignore
    <AppContext.Provider value={appNetwork} >
      {React.Children.map(
        children,
        Child => React.cloneElement(Child, props),
      )}
    </AppContext.Provider>
  );
}

/// Hook
/**
 * @desc
 * <p>
 * React hook for the global app state.
 * </p>
 * <p>
 * The arguments here follow the rules of
 * {@linkcode https://lodash.com/docs/#at|lodash.at}, except that object paths
 * which yield a singleton array will be reduced to a single value.
 * </p>
 * <p>
 * The returned state & bound action creator slices will be memoized against
 * the rest of the state, so state changes in an unrelated part of the state
 * will not cause unnecessary rerenders.
 * </p>
 *
 * @example
 > [ state['uri']['hash']['query'] ] === useAppState('uri.hash.query')
 > [ state['uri']['hash']['query'] ] === useAppState([ 'uri', 'hash', 'query' ])
 > [
 ...   [
 ...     state['uri']['hash']['query'],
 ...     state['uri']['hash']['aliases']
 ...   ]
 ... ] === useAppState(
 ...   [ 'uri.hash.query', 'uri.hash.aliases' ]
 ... )
 > [
 ...   [
 ...     state['uri']['hash']['query'],
 ...     state['uri']['hash']['aliases']
 ...   ],
 ...   [
 ...     boundActionCreators['setAppBatchReportJsonReport'],
 ...     boundActionCreators['setAppBatchReportFetchError'],
 ...   ],
 ... ] === useAppState(
 ...   [ 'uri.hash.query', 'uri.hash.aliases' ],
 ...   [ 'setAppBatchReportJsonReport', 'setAppBatchReportFetchError' ]
 ... )
 > [ state, boundActionCreators ] === useAppState(undefined, undefined) === useAppState()
 > [ undefined, boundActionCreators ] === useAppState(false) === useAppState(null)
 > [ undefined, undefined ] === useAppState(false, false)
 > [ state, undefined ] === useAppState(undefined, false)

 * @param {string | string[] | Array<string[]> | boolean} [stateSlices]
 *   - One or more object paths denoting the substate slice(s) to return, or
 *     a 'falsey' value to skip returning state at all. Note that skipping this
 *     parameter, or passing `undefined` explicitly will return the whole state
 *     object.
 * @param {string | string[] | Array<string[]> | boolean} [actionsSlices]
 *   - One or more bound action creators to return, or a 'falsey' value to skip
 *     returning any bound action creators state at all. Note that skipping this
 *     parameter, or passing `undefined` explicitly, will return all bound
 *     action creators.
 * @returns {[ ActuallyAny | ActuallyAny[], ActuallyAny | ActuallyAny[] ]}
 *   - Array of [ sliceOfState, sliceOfActions ]. `sliceOfState` and
 *     `sliceOfActions` are arrays if `stateSlices` and `actionsSlices`
 *     are non-singleton arrays, respectively
 */
export function useAppState(stateSlices, actionsSlices) {
  const context = useContext(AppContext);
  if(context === NOT_CHILD_OF_APP_CONTEXT_PROVIDER) {
    throw new Error('This component is not a child of `AppStateProvider`.');
  }
  const [ fullState, fullActions ] = context;
  const [ subState, subActions ] = [
    [ stateSlices, fullState ],
    [ actionsSlices, fullActions ],
  ].map(([ slice, full ]) => (
    // not defining a slice means return the whole object
    slice === undefined
      ? [ full ]
      : _at(full, slice)
  )).map(subArr => (
    // if the result of the above function is `[ val ]` reduce this to `val`
    Array.isArray(subArr) && subArr.length === 1
      ? subArr[0]
      : subArr
  ));

  // lodash.at returns a new object each time it's called, so we need to do a
  // deep comparison of the value previously returned from this hook and the
  // current value to determine whether we need a rerender
  const
    prevSubStateRef = useRef(subState),
    subStateDoRerender = !_isEqual(prevSubStateRef.current, subState),
    prevSubActionsRef = useRef(subActions),
    subActionDoRerender = !_isEqual(prevSubActionsRef.current, subActions);

  if(subStateDoRerender) prevSubStateRef.current = subState;
  if(subActionDoRerender) prevSubActionsRef.current = subActions;

  return [
    /* eslint-disable react-hooks/exhaustive-deps */
    useMemo(() => subState, [ subStateDoRerender ]),
    useMemo(() => subActions, [ subActionDoRerender ]),
    /* eslint-enable react-hooks/exhaustive-deps */
  ];
}
