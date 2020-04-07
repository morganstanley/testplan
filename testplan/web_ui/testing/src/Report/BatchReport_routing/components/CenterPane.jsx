import React from 'react';
import PropTypes from 'prop-types';

import AssertionPane from '../../../AssertionPane/AssertionPane';
import { COLUMN_WIDTH } from '../../../Common/defaults';
import Message from '../../../Common/Message';
import useReportState from '../hooks/useReportState';

/**
 * The center pane
 * @returns {React.FunctionComponentElement}
 */
export default function CenterPane() {
  const [
    [
      placeholderMessage = '', isFetchingMessage = '', isLoadingMessage = '',
      errorMessagePrelude = '',
      isFetching, isLoading, fetchError, selectedTestCase, jsonReport,
      filter,
    ]
  ] = useReportState([
    'centerPanelPlaceholderMessage', 'isFetchingMessage', 'isLoadingMessage',
    'fetchErrorMessagePrelude',
    'isFetching', 'isLoading', 'fetchError', 'selectedTestCase', 'jsonReport',
    'filter',
  ].map(e => `app.reports.batch.${e}`), false);
  const message =
    fetchError instanceof Error
      ? `${errorMessagePrelude} ${fetchError.message}`
      : isFetching
        ? isFetchingMessage
        : isLoading
          ? isLoadingMessage
          : null;
  if(message !== null) {
    return <Message left={COLUMN_WIDTH} message={message} />;
  } else if(selectedTestCase != null) {
    const
      { uid: testcaseUid,
        logs,
        entries: assertions,
        description,
      } = selectedTestCase,
      { uid: reportUid } = jsonReport,
      hasValidAssertions = Array.isArray(assertions) && assertions.length > 0,
      hasValidLogs = Array.isArray(logs) && logs.length > 0;
    if(hasValidAssertions || hasValidLogs) {
      return (
        <AssertionPane assertions={assertions}
                       logs={logs}
                       descriptionEntries={[description]}
                       left={COLUMN_WIDTH + 1.5}
                       testcaseUid={testcaseUid}
                       filter={filter}
                       reportUid={reportUid}
        />
      );
    }
  }
  return <Message left={COLUMN_WIDTH} message={placeholderMessage} />;
}
CenterPane.propTypes = {
  placeholderMessage: PropTypes.string,
  isFetchingMessage: PropTypes.string,
  isLoadingMessage: PropTypes.string,
  errorMessagePrelude: PropTypes.string,
  assertions: PropTypes.string,
  logs: PropTypes.any,
  filter: PropTypes.oneOf([ 'all', 'pass', 'fail' ]),
  reportUid: PropTypes.string,
  testcaseUid: PropTypes.string,
  description: PropTypes.string,
};
