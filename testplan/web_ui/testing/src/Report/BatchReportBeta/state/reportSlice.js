import _ from 'lodash';
import { createSlice } from '@reduxjs/toolkit';
import fetchReport from './reportActions/fetchReport';
import Axios from 'axios';

export default createSlice({
  name: 'report',
  initialState: {
    uid: null,
    document: null,
    isFetching: false,
    isFetchCancelled: false,
    fetchError: null,
    lastResponseContentLength: null,
  },
  reducers: {
    setReportUID: {
      reducer(state, { payload }) { state.uid = payload; },
      prepare: (uid = null) => ({ payload: uid }),
    },
    setLastResponseContentLength: {
      reducer(state, { payload }) {
        state.lastResponseContentLength = payload;
      },
      prepare: (contentLength = 0) => ({
        payload: _.isString(contentLength)
          ? parseInt(contentLength)
          : contentLength,
      }),
    },
  },
  extraReducers: {
    [fetchReport.pending.type](state) {
      state.isFetching = true;
      state.isFetchCancelled = false;
      state.fetchError = null;
    },
    [fetchReport.fulfilled.type](state, action) {
      state.isFetching = false;
      state.isFetchCancelled = false;
      state.fetchError = null;
      state.document = action.payload;
    },
    [fetchReport.rejected.type](state, action) {
      state.isFetching = false;
      if(_.isObject(action.error) && action.error.message === 'Rejected') {
        // handled with rejectWithValue
        const { payload: rejectValue } = action;
        state.isFetchCancelled = Axios.isCancel(rejectValue);
        state.fetchError = rejectValue;
      } else {
        state.isFetchCancelled = false;
        state.fetchError = action.error;
      }
    },
  },
});
