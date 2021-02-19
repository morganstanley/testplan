import {
  configureStore,
  combineReducers,
  getDefaultMiddleware,
} from '@reduxjs/toolkit';
import { setUseProxies } from 'immer';
import { fetchReport } from './reportActions';
import { getLastResponseContentLength } from './reportSelectors';
import { setSelectedEntry } from './uiActions';
import { flattened } from '../../../Common/utils';

const __DEV__ = process.env.NODE_ENV !== 'production';

// At @reduxjs/toolkit/dist/redux-toolkit.esm.js:1422 (@reduxjs/toolkit@1.3.4)
// ES5 compatibility is enabled, which switches off Proxy support, which is bad:
// https://immerjs.github.io/immer/docs/performance#:~:text=The%20ES5%20fallback%20implementation
setUseProxies(true);

const createReducer = () => combineReducers({
  // eslint-disable-next-line max-len
  report: require('./reportSlice').default.reducer,
  ui: require('./uiSlice').default.reducer,
});

let devTools = false;
const middlewareOptions = {
  serializableCheck: false,
  immutableCheck: false,
};

if(__DEV__) {
  const FIX_DEVTOOL_SPEED = process.env.REACT_APP_FIX_DEVTOOL_SPEED === 'true';
  // eslint-disable-next-line max-len
  const DISABLE_REDUX_DEVTOOLS = process.env.REACT_APP_DISABLE_REDUX_DEVTOOLS === 'true';
  let shaveObjectEntriesFromObject = null;
  if(__DEV__ && FIX_DEVTOOL_SPEED && !DISABLE_REDUX_DEVTOOLS) {
    console.warn(flattened`
    You've set the environment variable REACT_APP_FIX_DEVTOOL_SPEED=true
    which will disable several features in Redux Devtools.
  `);
    const _ = require('lodash');
    shaveObjectEntriesFromObject = (entry, placeholder = '<<omitted>>') => (
      !_.isObjectLike(entry) ? entry : Object.fromEntries(
        Object.entries(entry).map(([ prop, val ]) => [
          prop, _.isObjectLike(val)
            ? _.isFunction(placeholder) ? placeholder(prop, val) : placeholder
            : val
        ])
      ));
  }

  devTools = !DISABLE_REDUX_DEVTOOLS && (!FIX_DEVTOOL_SPEED ? true : {
    name: 'testplan',
    maxAge: 10,
    trace: true,
    traceLimit: 3,
    shouldCatchErrors: true,
    shouldRecordChanges: true,
    shouldHotReload: true,
    actionSanitizer: action => {
      switch(action.type) {
        case fetchReport.fulfilled.type:
          return { ...action, payload: '<<omitted>>' };
        case setSelectedEntry.type:
          return { ...action, payload: shaveObjectEntriesFromObject
            ? shaveObjectEntriesFromObject(action.payload)
            : action.payload
          };
        default:
          return action;
      }
    },
    stateSanitizer: state => {
      // devtools crashes and the UI freezes at 45_864_416 so this number can
      // likely be tuned up or down (right now it's just a guess)
      if(35_000_000 < getLastResponseContentLength(state)) {
        // these slow down the extension - and hence the UI - a lot
        window.__CURRENT_REPORT = state.report.document;
        window.__SELECTED_ENTRY = state.ui.selectedEntry;
        return {
          ...state,
          report: {
            ...state.report,
            document: '<<available on window.__CURRENT_REPORT>>',
          },
          ui: {
            ...state.ui,
            selectedEntry: shaveObjectEntriesFromObject
              ? shaveObjectEntriesFromObject(
                  state.ui.selectedEntry,
                  key => `<<available on window.__SELECTED_ENTRY.${key}>>`
                )
              : state.ui.selectedEntry,
          },
        };
      }
      return state;
    },
  });

  middlewareOptions.serializableCheck = !FIX_DEVTOOL_SPEED ? true : ({
    ignoredPaths: [ 'report.document', 'ui.selectedEntry' ],
    ignoredActions: [
      fetchReport.fulfilled.type,
      setSelectedEntry.type,
    ],
  });

  middlewareOptions.immutableCheck = !FIX_DEVTOOL_SPEED ? true : ({
    ignoredPaths: [ 'report.document', 'ui.selectedEntry' ],
  });
}

const store = configureStore({
  reducer: createReducer(),
  middleware: getDefaultMiddleware(middlewareOptions),
  devTools,
});

if(__DEV__ && module && module.hot) {
  module.hot.accept(() => store.replaceReducer(createReducer()));
}

export default store;
