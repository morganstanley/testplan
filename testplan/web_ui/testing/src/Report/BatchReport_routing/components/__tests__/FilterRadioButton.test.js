/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';
import _zip from 'lodash/zip';
import FilterRadioButton from '../FilterRadioButton';
import useReportState from '../../hooks/useReportState';

jest.mock('../../hooks/useReportState');

const FILTER_RADIO_LABEL = 'FILTER_RADIO_LABEL';
const AVAIL_FILTERS = [ 'a', 'b', 'c' ];
const FILTER_VALUE_COMBOS = AVAIL_FILTERS.reduce(
  (prev, filter) => prev.concat(_zip(
    /* value */ Array.from({ length: AVAIL_FILTERS.length }, () => filter),
    /* filter */ AVAIL_FILTERS,
  )),
  []
);

describe('FilterRadioButton', () => {

  beforeEach(() => {
    useReportState.mockName('useReportState');
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it.each(_shuffle(FILTER_VALUE_COMBOS))(
    'is checked only when filter === value, given { value: %j, filter: %j }',
    (value, filter) => {
      useReportState.mockReturnValue([ filter, jest.fn() ]);
      const { container } = render(
        <FilterRadioButton label={FILTER_RADIO_LABEL} value={value} />
      );
      const checkboxes = container.querySelectorAll('input[type="radio"]');
      expect(checkboxes).toHaveLength(1);
      expect(checkboxes[0].checked).toBe(value === filter);
    },
  );

  it.each(_shuffle(FILTER_VALUE_COMBOS))(
    'renders correctly when { value: %j, filter: %j }',
    (value, filter) => {
      useReportState.mockReturnValue([ filter, jest.fn() ]);
      expect(render(
        <FilterRadioButton label={FILTER_RADIO_LABEL} value={value} />
      ).container).toMatchSnapshot();
    });

  it('grabs correct slices from useReportState', () => {
    const expectedHookArgs = [
      'app.reports.batch.filter',
      'setAppBatchReportFilter',
    ];
    useReportState.mockReturnValue([
      false, jest.fn().mockName(expectedHookArgs[1])
    ]);
    render(<FilterRadioButton label={FILTER_RADIO_LABEL} />);
    expect(useReportState).toHaveBeenCalledTimes(1);
    expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
  });

  it.each(_shuffle(AVAIL_FILTERS))(
    'clicking radio calls `setAppBatchReportFilter(%j)`',
    (value) => {
      const expectedHookArgs = [
        'app.reports.batch.filter',
        'setAppBatchReportFilter',
      ];
      const setFilter = jest.fn().mockName(expectedHookArgs[1]);
      useReportState.mockReturnValue([ 'x', setFilter ]);
      const { container } = render(
        <FilterRadioButton label={FILTER_RADIO_LABEL} value={value} />
      );
      expect(useReportState).toHaveBeenCalledTimes(1);
      expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
      const radioBtn = container.querySelector('input[type="radio"]');
      fireEvent.click(radioBtn);
      expect(setFilter).toHaveBeenCalledTimes(1);
      expect(setFilter).toHaveBeenLastCalledWith(value);
    },
  );

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    jest.resetAllMocks();
  });

});
