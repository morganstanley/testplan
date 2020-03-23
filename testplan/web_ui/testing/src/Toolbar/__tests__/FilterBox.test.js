import React from 'react';
import { shallow } from 'enzyme';
import { StyleSheetTestUtils } from "aphrodite";

import FilterBox from '../FilterBox';

function defaultProps() {
  return {
    width: '19.5em',
    handleNavFilter: jest.fn(),
  };
}

describe('FilterBox', () => {
  let props;
  let mountedFilterBox;
  const renderFilterBox = () => {
    if (!mountedFilterBox) {
      mountedFilterBox = shallow(
        <FilterBox {...props} />
      );
    }
    return mountedFilterBox;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedFilterBox = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.handleNavFilter.mockClear();
  });

  it('shallow renders without crashing', () => {
    renderFilterBox();
  });

  it('shallow renders the correct HTML structure', () => {
    const filterBox = renderFilterBox();
    expect(filterBox).toMatchSnapshot();
  });

  it('calls handleNavFilter when onKeyUp event is triggered ' +
     'for input box', () => {
    const handleNavFilter = props.handleNavFilter;
    const filterBox = renderFilterBox();

    filterBox.find('input').simulate('keyUp', {keyCode: 13, key: 'Enter'});
    expect(handleNavFilter.mock.calls.length).toEqual(1);
  })

});