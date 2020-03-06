import React from 'react';
import { connect } from 'react-redux';
import { createSelector } from '@reduxjs/toolkit';
import {
  mkGetUIFilter,
  mkGetUISelectedEntry,
  mkGetUISidebarWidthFirstAvailable,
} from '../state/uiSelectors';
import {
  mkGetReportDocument,
  mkGetReportIsFetching,
  mkGetReportLastFetchError,
} from '../state/reportSelectors';
import AssertionPane from '../../../AssertionPane/AssertionPane';
import Message from '../../../Common/Message';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import { isNonemptyArray } from '../../../Common/utils';
import _ from 'lodash';

const STARTING_MSG = 'Waiting to fetch Testplan report...';
const FETCHING_MSG = 'Fetching Testplan report...';
const FINISHED_MSG = 'Please select an entry.';
const ERRORED_PREFIX_MSG = 'Error fetching Testplan report';
// using a static placeholder - rather than creating a new one every time in
// connect or the component - will help prevent unnecessary rerenders since
// we'll maintain the same referential identity
const SELECTED_ENTRY_PLACEHOLDER = {
  uid: '',
  category: '',
  logs: [],
  entries: [],
  description: [],
};

const placeholderConnector = connect(
  () => {
    const getDocument = mkGetReportDocument();
    const getIsFetching = mkGetReportIsFetching();
    const getError = mkGetReportLastFetchError();
    return function mapStateToProps(state) {
      const isFetching = getIsFetching(state);
      const error = getError(state);
      const document = getDocument(state);
      let message = STARTING_MSG;
      if(!isFetching && error) {
        message = _.isObject(error)
          ? `${ERRORED_PREFIX_MSG}: ${error.message}`
          : `${ERRORED_PREFIX_MSG}.`;
      } else if(isFetching) {
        message = FETCHING_MSG;
      } else if(!isFetching && !error && _.isObject(document)) {
        message = FINISHED_MSG;
      }
      return { message };
    };
  }
);

const Placeholder = ({ message, left }) => (
  <Message left={left} message={message} />
);

const ConnectedPlaceholder = placeholderConnector(Placeholder);

const centerPaneConnector = connect(
  () => {
    const getFilter = mkGetUIFilter();
    const getSelectedEntrySafe = createSelector(
      mkGetUISelectedEntry(),
      entry => (entry || {})
    );
    const getReportUID = createSelector(
      mkGetReportDocument(),
      document => (document || {}).uid,
    );
    const getSidebarWidth = mkGetUISidebarWidthFirstAvailable();
    return function mapStateToProps(state) {
      const selectedEntry = getSelectedEntrySafe(state);
      return {
        filter: getFilter(state),
        selectedEntry: selectedEntry.category === BOTTOMMOST_ENTRY_CATEGORY
          ? selectedEntry
          : SELECTED_ENTRY_PLACEHOLDER,
        reportUID: getReportUID(state),
        left: getSidebarWidth(state),
      };
    };
  },
);

const CenterPane = ({ selectedEntry, reportUID, filter, left }) => {
  const { uid, category, logs, entries, description } = selectedEntry;
  const descriptionEntries = React.useMemo(() => (
    isNonemptyArray(description) ? description : [ description ]
  ).filter(Boolean), [ description ]);
  if(category === BOTTOMMOST_ENTRY_CATEGORY) {
    return (
      <AssertionPane assertions={entries}
                     logs={logs}
                     descriptionEntries={descriptionEntries}
                     left={left}
                     testcaseUid={uid}
                     filter={filter}
                     reportUid={reportUID}
      />
    );
  }
  return <ConnectedPlaceholder left={left}/>;
};

export default centerPaneConnector(CenterPane);
