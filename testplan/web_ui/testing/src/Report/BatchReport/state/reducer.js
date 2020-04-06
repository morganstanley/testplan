import * as actionTypes from './actionTypes';
import * as actionChangeTypes from './actionChangeTypes';
import produce, { enableMapSet } from 'immer';
enableMapSet();  // allows the reducer to use Map and Set

export default produce((draftState, action) => {
  // default case not needed, see immerjs.github.io/immer/docs/example-reducer
  /* eslint-disable default-case */
  switch(action.type) {
    case actionTypes.IS_TESTING:
      switch(action.change) {
        case actionChangeTypes.REPLACE:
        case actionChangeTypes.PATCH:
          const { isTesting } = action.payload;
          draftState.isTesting = isTesting;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_DO_AUTO_SELECT:
      switch(action.change) {
        case actionChangeTypes.REPLACE:
        case actionChangeTypes.PATCH:
          const { doAutoSelect } = action.payload;
          draftState.app.reports.batch.doAutoSelect = doAutoSelect;
          break;
      }
      break;
    case actionTypes.URI_HASH_ALIASES:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { alias, component } = action.payload;
          draftState.uri.hash.aliases.set(alias, component);
          break;
      }
      break;
    case actionTypes.URI_HASH_QUERY:
      switch(action.change) {
        case actionChangeTypes.REPLACE:
          draftState.uri.hash.query.clear();
        // eslint-disable-next-line no-fallthrough
        case actionChangeTypes.PATCH:
          for(const [param, val] of action.payload.mapping) {
            draftState.uri.hash.query.set(param, val);
          }
          break;
        case actionChangeTypes.DELETE:
          for(const param of action.payload.values) {
            draftState.uri.hash.query.delete(param);
          }
          break;
      }
      break;
    case actionTypes.URI_QUERY:
      switch(action.change) {
        case actionChangeTypes.REPLACE:
          draftState.uri.query.clear();
        // eslint-disable-next-line no-fallthrough
        case actionChangeTypes.PATCH:
          for(const [param, val] of action.payload.mapping) {
            draftState.uri.query.set(param, val);
          }
          break;
        case actionChangeTypes.DELETE:
          for(const param of action.payload.values) {
            draftState.uri.query.delete(param);
          }
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_DISPLAY_EMPTY:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isDisplayEmpty } = action.payload;
          draftState.app.reports.batch.isDisplayEmpty = isDisplayEmpty;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_FILTER:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { filter } = action.payload;
          draftState.app.reports.batch.filter = filter;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_FETCHING:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isFetching } = action.payload;
          draftState.app.reports.batch.isFetching = isFetching;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_LOADING:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isLoading } = action.payload;
          draftState.app.reports.batch.isLoading = isLoading;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_FETCH_ERROR:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { fetchError } = action.payload;
          draftState.app.reports.batch.fetchError = fetchError;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_SHOW_TAGS:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isShowTags } = action.payload;
          draftState.app.reports.batch.isShowTags = isShowTags;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_JSON_REPORT:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { jsonReport } = action.payload;
          draftState.app.reports.batch.jsonReport = jsonReport;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_SHOW_HELP_MODAL:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isShowHelpModal } = action.payload;
          draftState.app.reports.batch.isShowHelpModal = isShowHelpModal;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_SHOW_INFO_MODAL:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { isShowInfoModal } = action.payload;
          draftState.app.reports.batch.isShowInfoModal = isShowInfoModal;
          break;
      }
      break;
    case actionTypes.APP_BATCHREPORT_SELECTED_TEST_CASE:
      switch(action.change) {
        case actionChangeTypes.PATCH:
        case actionChangeTypes.REPLACE:
          const { selectedTestCase } = action.payload;
          draftState.app.reports.batch.selectedTestCase = selectedTestCase;
          break;
      }
      break;
  }
  /* eslint-enable default-case */
  if(typeof action.callback === 'function') {
    action.callback(draftState);
  }
});
