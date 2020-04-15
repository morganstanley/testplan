/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { StyleSheetTestUtils } from 'aphrodite';
import HelpModal from '../HelpModal';
import useReportState from '../../hooks/useReportState';

jest.mock('../../hooks/useReportState');

describe('HelpModal', () => {

  beforeEach(() => {
    // Jest doesn't clean up the JSDOM between tests. In these tests, this
    // results in us having either `<body>...</body>` or
    // `<body class="">...</body>` depending upon the order of the snapshots,
    // meaning that the snapshots are not idempotent. This `removeAttribute` is
    //  an inelegant patch for this.
    window.document.body.removeAttribute('class');
    useReportState.mockName('useReportState');
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders as expected when modal is showing', () => {
    useReportState.mockReturnValue([ true, jest.fn() ]);
    const { baseElement } = render(<HelpModal/>);
    /**
     * We snapshot `baseElement` instead of the `container`
     * container because reactstrap/lib/Modal* uses createPortal which renders
     * above our container element.
     * @see https://reactjs.org/docs/portals.html
     * @see https://github.com/testing-library/react-testing-library/issues/62
     */
    expect(baseElement).toMatchSnapshot();
  });

  it('renders as expected when modal is NOT showing', () => {
    useReportState.mockReturnValue([ false, jest.fn() ]);
    const { baseElement } = render(<HelpModal/>);
    expect(baseElement).toMatchSnapshot();
  });

  it('grabs correct slices from useReportState', () => {
    const expectedHookArgs = [
      'app.reports.batch.isShowHelpModal',
      'setAppBatchReportShowHelpModal',
    ];
    useReportState.mockReturnValue([
      false, jest.fn().mockName(expectedHookArgs[1])
    ]);
    render(<HelpModal/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
  });

  it('"Close" button calls `setAppBatchReportShowHelpModal`', () => {
    const expectedHookArgs = [
      'app.reports.batch.isShowHelpModal',
      'setAppBatchReportShowHelpModal',
    ];
    const setShowHelpModal = jest.fn().mockName(expectedHookArgs[1]);
    const isShowHelpModal = true;
    useReportState.mockReturnValue([ isShowHelpModal, setShowHelpModal ]);
    const { getAllByText } = render(<HelpModal/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
    const closeBtns = getAllByText('Close', { selector: 'button' });
    expect(closeBtns).toHaveLength(1);
    fireEvent.click(closeBtns[0]);
    expect(setShowHelpModal).toHaveBeenCalledTimes(1);
    expect(setShowHelpModal).toHaveBeenLastCalledWith(!isShowHelpModal);
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    jest.resetAllMocks();
  });

});
