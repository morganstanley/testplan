/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';
import DisplayEmptyCheckBox from '../DisplayEmptyCheckBox';
import useReportState from '../../hooks/useReportState';

jest.mock('../../hooks/useReportState');
const DISPLAY_EMPTY_LABEL = 'DISPLAY_EMPTY_LABEL';

describe('DisplayEmptyCheckBox', () => {

  beforeEach(() => {
    useReportState.mockName('useReportState');
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it.each(_shuffle([ true, false ]))(
    'renders as expected when .checked === `isDisplayEmpty` === %j',
    (isDisplayEmpty) => {
      const setDisplayEmpty = jest.fn();
      useReportState.mockReturnValue([ isDisplayEmpty, setDisplayEmpty ]);
      const { container } = render(
        <DisplayEmptyCheckBox label={DISPLAY_EMPTY_LABEL}/>
      );
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes).toHaveLength(1);
      expect(checkboxes[0].checked).toBe(!isDisplayEmpty);
      expect(container).toMatchSnapshot();
    },
  );

  it('grabs correct slices from useReportState', () => {
    const expectedHookArgs = [
      'app.reports.batch.isDisplayEmpty',
      'setAppBatchReportIsDisplayEmpty',
    ];
    useReportState.mockReturnValue([
      false, jest.fn().mockName(expectedHookArgs[1])
    ]);
    render(<DisplayEmptyCheckBox label={DISPLAY_EMPTY_LABEL}/>);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
  });

  it('clicking checkbox calls `setAppBatchReportIsDisplayEmpty`', () => {
    const expectedHookArgs = [
      'app.reports.batch.isDisplayEmpty',
      'setAppBatchReportIsDisplayEmpty',
    ];
    const setDisplayEmpty = jest.fn().mockName(expectedHookArgs[1]);
    const isDisplayEmpty = true;
    useReportState.mockReturnValue([ isDisplayEmpty, setDisplayEmpty ]);
    const { container } = render(
      <DisplayEmptyCheckBox label={DISPLAY_EMPTY_LABEL}/>
    );
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
    const checkbox = container.querySelector('input[type="checkbox"]');
    fireEvent.click(checkbox);
    expect(setDisplayEmpty).toHaveBeenCalledTimes(1);
    expect(setDisplayEmpty).toHaveBeenLastCalledWith(!isDisplayEmpty);
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    jest.resetAllMocks();
  });

});
