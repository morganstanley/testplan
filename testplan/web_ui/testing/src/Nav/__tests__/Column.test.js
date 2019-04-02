import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import Column from '../Column';

describe('Column', () => {
  let mountedColumn;
  const renderColumn = () => {
    if (!mountedColumn) {
      mountedColumn = shallow(
        <Column>
          <p className='unique' />
        </Column>
      );
    }
    return mountedColumn;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    mountedColumn = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('shallow renders without crashing', () => {
    renderColumn();
  });

  it('shallow renders the correct HTML structure', () => {
    const column = renderColumn();
    expect(column).toMatchSnapshot();
  });

});