/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { shallow } from 'enzyme';
import { StyleSheetTestUtils } from 'aphrodite';
import InfoModal from '../InfoModal';
import useReportState from '../../hooks/useReportState';

jest.mock('../../hooks/useReportState');

describe('InfoModal', () => {

  beforeAll(() => {
    useReportState.mockName('useReportState');
  });

  beforeEach(() => {
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it('renders as expected when modal is showing', () => {
    useReportState.mockReturnValue([ true, jest.fn() ]);
    // we're using `shallow` because we don't want the results of these tests
    // to depend upon the child component <InfoTable/>
    const wrapper = shallow(<InfoModal/>);
    expect(wrapper).toMatchSnapshot();
  });

  it('renders as expected when modal is NOT showing', () => {
    useReportState.mockReturnValue([ false, jest.fn() ]);
    const wrapper = shallow(<InfoModal/>);
    expect(wrapper).toMatchSnapshot();
  });

  it('grabs correct slices from useReportState', () => {
    const expectedHookArgs = [
      'app.reports.batch.isShowInfoModal',
      'setAppBatchReportShowInfoModal',
    ];
    useReportState.mockReturnValue([
      false, jest.fn().mockName(expectedHookArgs[1])
    ]);
    shallow(<InfoModal/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
  });

  it('"Close" button calls `setAppBatchReportShowInfoModal`', () => {
    const expectedHookArgs = [
      'app.reports.batch.isShowInfoModal',
      'setAppBatchReportShowInfoModal',
    ];
    const setShowInfoModal = jest.fn().mockName(expectedHookArgs[1]);
    const isShowInfoModal = true;
    useReportState.mockReturnValue([ isShowInfoModal, setShowInfoModal ]);
    const wrapper = shallow(<InfoModal/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
    wrapper.find('Button').simulate('click');
    expect(setShowInfoModal).toHaveBeenCalledTimes(1);
    expect(setShowInfoModal).toHaveBeenLastCalledWith(!isShowInfoModal);
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    jest.resetAllMocks();
  });

});
