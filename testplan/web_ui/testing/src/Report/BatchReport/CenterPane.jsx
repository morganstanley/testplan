import React from 'react';
import AssertionPane from '../../AssertionPane/AssertionPane';
import { COLUMN_WIDTH } from '../../Common/defaults';
import Message from '../../Common/Message';
import PropTypes from 'prop-types';
import { useAppState } from './state';

/**
 * @typedef FilterStates
 * @property {"all"} ALL
 * @property {"fail"} FAILED
 * @property {"pass"} PASSED
 * @readonly
 */

/**
 * The center pane
 * @param {React.PropsWithoutRef} p
 * @param {string} [p.placeholderMessage="Please select an entry."]
 * @param {string} [p.isFetchingMessage="Fetching Testplan report..."]
 * @param {string} [p.isLoadingMessage="Waiting to fetch Testplan report..."]
 * @param {string} [p.errorMessagePrelude="Error fetching Testplan report."]
 * @param {unknown} [p.assertions]
 * @param {unknown} [p.logs]
 * @param {FilterStates} [p.filter]
 * @param {string} [p.reportUid]
 * @param {string} [p.testcaseUid]
 * @param {string} [p.description]
 * @returns {React.FunctionComponentElement}
 */
export default function CenterPane({
  placeholderMessage = 'Please select an entry.',
  isFetchingMessage = 'Fetching Testplan report...',
  isLoadingMessage = 'Waiting to fetch Testplan report...',
  errorMessagePrelude = 'Error fetching Testplan report.',
  /*assertions, logs, filter, reportUid, testcaseUid, description,*/
}) {
  const [[
    isFetching, isLoading, fetchError, selectedTestCase, jsonReport,
    filter
  ]] = useAppState([
    'isFetching', 'isLoading', 'fetchError', 'selectedTestCase', 'jsonReport',
    'filter',
  ].map(e => `app.reports.batch.${e}`), false);

  placeholderMessage = placeholderMessage || '';
  isFetchingMessage = isFetchingMessage || '';
  isLoadingMessage = isLoadingMessage || '';
  errorMessagePrelude = errorMessagePrelude || '';

  const message =
    isFetching ?
      isFetchingMessage
      : fetchError instanceof Error ?
        `${errorMessagePrelude} ${fetchError.message}`
        : isLoading ?
          isLoadingMessage
          : null;

  if(message !== null) {
    return <Message left={COLUMN_WIDTH} message={message} />;
  } else if(selectedTestCase != null) {
    const
      {
        uid: testcaseUid,
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
