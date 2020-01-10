import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import NavBreadcrumbs from '../NavBreadcrumbs';

function defaultProps() {
  const entry = {
    uid: '123',
    name: 'test',
    status: 'passed',
    category: 'testplan',
    counter: {
      passed: 0,
      failed: 0,
    },
  };
  return {
    entries: [entry],
    handleNavClick: jest.fn(),
  };
}

describe('NavBreadcrumbs', () => {
  const props = defaultProps();

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.handleNavClick.mockClear();
  });

  it('shallow renders the correct HTML structure', () => {
    const navBreadcrumbs = shallow(
        <NavBreadcrumbs {...props} />
    );
    expect(navBreadcrumbs).toMatchSnapshot();
  });

  it('calls handleNavClick when nav entry has been clicked', () => {
    const handleNavClick = props.handleNavClick;
    const navBreadcrumbs = shallow(
      <NavBreadcrumbs {...props} />
    );

    navBreadcrumbs.find('li').simulate('click');
    expect(handleNavClick.mock.calls.length).toEqual(1);
  });
});
