import { createAsyncThunk } from '@reduxjs/toolkit';
import Axios from 'axios';
import { headers as defaultHeaders } from 'axios/lib/defaults';
import _ from 'lodash';
import {
  getReportUid,
  getReportIsFetching,
  getReportDocument,
  getReportLastFetchError,
  getReportIsFetchCancelled,
} from '../reportSelectors';
import { PropagateIndices } from '../../../reportUtils';
import { toPlainObjectIn, flattened } from '../../../../Common/utils';

const __DEV__ = process.env.NODE_ENV !== 'production';
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
const UNSET_API_BASE_URL_VAL = 'OverrideMeOrThereWillBeABuildError';
/** @type {URL} */
const API_BASE_URL_OBJ = (() => {
  // these conditionals + try-catches are top-level so errors will be caught 
  // during the build.
  // eslint-disable-next-line max-len
  if(!_.isString(API_BASE_URL) || API_BASE_URL === UNSET_API_BASE_URL_VAL) {
    throw new Error(
      "The environment variable REACT_APP_API_BASE_URL must be set to your " +
      "API's base URL. See this project's .env file for more information."
    );
  }
  let apiBaseUrlObj;
  try {
    // this will not error when API_BASE_URL is a full URI
    apiBaseUrlObj = new URL(API_BASE_URL);
  } catch(err1) {
    try {
      // this will not error when API_BASE_URL only a path
      apiBaseUrlObj = new URL(API_BASE_URL, window.location.origin);
    } catch(err2) {
      throw new Error(
        `The environment variable REACT_APP_API_BASE_URL is not set to a ` +
        `valid URL or a URL path - received ` +
        `REACT_APP_API_BASE_URL="${API_BASE_URL}".`
      );
    }
  }
  return apiBaseUrlObj;
})();

let TEST_REPORTS = {};  // eslint-disable-line no-unused-vars
if(__DEV__) {
  TEST_REPORTS = {
    fakeReport: require('../../../../Common/fakeReport'),
    sampleReports: require('../../../../Common/sampleReports'),
  };
}

const axiosDefaultConfig = (() => {
  const apiBaseURLOrigin = API_BASE_URL_OBJ.origin;
  const apiBaseURL = API_BASE_URL_OBJ.href;
  const headers = { ...defaultHeaders.common, Accept: 'application/json' };
  if(__DEV__ && window.location.origin !== apiBaseURLOrigin) {
    headers['Access-Control-Allow-Origin'] = apiBaseURLOrigin;
  }
  return { baseURL: apiBaseURL, headers, timeout: 60_000 };
})();

const fetchFakeReport = async ({ testReport }, { dispatch, requestId }) => {
  const { setReportUID } = await import('./');
  dispatch(setReportUID(testReport));
  const data = await _.get(TEST_REPORTS, testReport, requestId);
  if(data === requestId) throw new Error(flattened`
    Invalid object path "${testReport}", valid paths are
  `);
  return { data, headers: { 'content-length': JSON.stringify(data).length } };
};

const fetchRemoteReport = async ({ axios: mockAxios, uid }, thunkAPI) => {
  const { dispatch, signal } = thunkAPI;
  const { setReportUID } = await import('./');
  // setup fetch
  dispatch(setReportUID(uid));
  let axiosInstance, cancelFunc, cancelToken, abortListenerID = -1;
  if(_.isObject(mockAxios)) {
    axiosInstance = mockAxios;
    if(_.isObject(axiosInstance.defaults.cancelToken)) {
      cancelToken = axiosInstance.defaults.cancelToken.token;
    }
  } else {
    const cancelSource = Axios.CancelToken.source();
    cancelFunc = cancelSource.cancel;
    cancelToken = cancelSource.token;
    axiosInstance = Axios.create({ ...axiosDefaultConfig, cancelToken });
  }
  if(_.isFunction(cancelFunc)) signal.addEventListener('abort', () => {
    cancelFunc('The fetch was cancelled.');
  });
  if(_.isObject(cancelToken)) abortListenerID = setInterval(() => {
    cancelToken.throwIfRequested();
  }, 10);
  // execute fetch, see https://github.com/axios/axios#response-schema
  return await axiosInstance.get(`/${uid}`).finally(() => {
    if(abortListenerID > 0) clearInterval(abortListenerID);
  });
};

/** This function keeps duplicate fetches from occurring */
const checkShouldAcceptFetchRequest = ({ uid }, { getState }) => {
  if(uid !== getReportUid(getState())) return true;
  if(getReportIsFetching(getState())) return false;
  if(_.isObject(getReportDocument(getState()))) return (
    !_.isNil(getReportLastFetchError(getState())) ||
    getReportIsFetchCancelled(getState())
  );
};

/**
 * During testing / development it's possible to pass in the path to one
 * of the promises in the following object and return it instead of actually
 * doing a fetch
 * @example
     fetchReport({ testReport: 'fakeReport.TESTPLAN_REPORT' })

 * @param {object} arg
 * @param {string} arg.uid
 * @param {object=} arg.axios
 * @param {object=} arg.testReport
 * @returns {{ abort(): void }}
 */
const fetchReport = createAsyncThunk(
  'report/fetchReport',
  async (arg, thunkAPI) => {
    const { dispatch, rejectWithValue, requestId } = thunkAPI;
    try {
      if(!_.isPlainObject(arg))
        throw new class extends Error { name = 'FetchReportArgError'; }(
          __DEV__ ? '`fetchReport` takes a single plain object argument'
                  : 'Contact support'
        );
      const { setLastResponseContentLength } = await import('./');
      const { headers, data } = await (
        __DEV__ && _.isString(arg.testReport)
          ? fetchFakeReport(arg, { dispatch, requestId })
          : fetchRemoteReport(arg, thunkAPI)
      );
      dispatch(setLastResponseContentLength(headers['content-length']));
      return PropagateIndices(data);
    } catch(err) {
      return rejectWithValue(
        Axios.isCancel(err)
          ? _.toPlainObject(err)
          : toPlainObjectIn(err)
      );
    }
  },
  {
    condition: checkShouldAcceptFetchRequest,
    dispatchConditionRejection: false,
  }
);

export default fetchReport;
