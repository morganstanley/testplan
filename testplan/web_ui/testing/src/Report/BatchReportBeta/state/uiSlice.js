import { createSlice } from '@reduxjs/toolkit/dist';
import * as filterStates from '../../../Common/filterStates';
import { fetchReport } from './reportActions';
import { COLUMN_WIDTH } from '../../../Common/defaults';

const FILTER_STATES_ARR = Object.values(filterStates);

/** This state slice contains information specific to how the UI should look */
export default createSlice({
  name: 'ui',
  initialState: {
    isShowHelpModal: false,
    isDisplayEmpty: true,
    filter: filterStates.ALL,
    isShowTags: false,
    isShowInfoModal: false,
    selectedEntry: null,
    sidebarWidthPx: null,
    sidebarWidthEm: `${COLUMN_WIDTH}em`,
  },
  reducers: {
    setSelectedEntry: {
      reducer(state, action) { state.selectedEntry = action.payload; },
      prepare: (entry = null) => ({ payload: entry }),
    },
    setSidebarWidth: {
      reducer(state, { payload }) { state.sidebarWidthPx = payload; },
      prepare: (widthPxStr) => ({ payload: widthPxStr }),
    },
    setShowTags: {
      reducer(state, { payload }) { state.isShowTags = payload; },
      prepare: (showTags = false) => ({ payload: !!showTags }),
    },
    setShowInfoModal: {
      reducer(state, { payload }) { state.isShowInfoModal = payload; },
      prepare: (showInfoModal = false) => ({ payload: !!showInfoModal }),
    },
    setFilter: {
      reducer(state, { payload }) { state.filter = payload; },
      prepare: (filter = filterStates.ALL) => ({
        payload: FILTER_STATES_ARR.includes(filter) ? filter : filterStates.ALL
      }),
    },
    setDisplayEmpty: {
      reducer(state, { payload }) { state.isDisplayEmpty = payload; },
      prepare: (displayEmpty = true) => ({ payload: !!displayEmpty }),
    },
    setShowHelpModal: {
      reducer(state, { payload }) { state.isShowHelpModal = payload; },
      prepare: (showHelpModal = false) => ({ payload: !!showHelpModal }),
    },
  },
  extraReducers: {
    [fetchReport.fulfilled.type](state, action) {
      state.selectedEntry = action.payload;
    },
  },
});
