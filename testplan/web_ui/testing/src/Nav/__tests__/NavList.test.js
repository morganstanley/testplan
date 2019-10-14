import React from 'react';
import {ListGroupItem} from 'reactstrap';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import NavList from '../NavList';

function defaultProps() {
  const entry = {
    uid: '123',
    name: 'test',
    status: 'passed',
    type: 'testplan',
    case_count: {
      passed: 1,
      failed: 0,
    },
    filter: 'all',
    displayEmpty: true,
    displayTags: true,
  };
  return {
    entries: [entry],
    breadcrumbLength: 1,
    handleNavClick: jest.fn(),
  };
}

describe('NavList', () => {
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

  it('shallow renders and matches snapshot', () => {
    const nav_list = shallow(
      <NavList {...props} />
    );
    expect(nav_list).toMatchSnapshot();
  });

  it('calls handleNavClick when nav entry has been clicked', () => {
    const handle_nav_click = props.handleNavClick;
    const nav_list = shallow(
      <NavList {...props} />
    );

    nav_list.find(ListGroupItem).simulate('click');
    expect(handle_nav_click.mock.calls.length).toEqual(1);
  })
});
