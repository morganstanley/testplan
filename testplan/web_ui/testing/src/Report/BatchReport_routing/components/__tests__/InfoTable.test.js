/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render } from '@testing-library/react';
import { StyleSheetTestUtils } from 'aphrodite';
import InfoTable from '../InfoTable';
import useReportState from '../../hooks/useReportState';
import { filterObjectDeep } from '../../../../__tests__/fixtures/testUtils';

jest.mock('../../hooks/useReportState');

const TESTPLAN_REPORT_2 =
  require('../../../../__tests__/mocks/documents/TESTPLAN_REPORT_2.json');
const TESTPLAN_REPORT_2_SLIM = filterObjectDeep(
  TESTPLAN_REPORT_2,
  [ 'information', 'timer', 'run', 'start', 'end' ]
);

describe('InfoTable', () => {

  beforeEach(() => {
    useReportState.mockName('useReportState');
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders as expected', () => {
    useReportState.mockReturnValue([ TESTPLAN_REPORT_2_SLIM ]);
    const { container } = render(<InfoTable/>);
    expect(container).toMatchSnapshot();
  });

  it('grabs correct slices from useReportState', () => {
    const expectedHookArgs = [ 'app.reports.batch.jsonReport', false ];
    useReportState.mockReturnValue([ TESTPLAN_REPORT_2_SLIM ]);
    render(<InfoTable/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    jest.resetAllMocks();
  });

});
