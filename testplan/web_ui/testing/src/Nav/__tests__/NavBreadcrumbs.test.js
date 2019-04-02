import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import NavBreadcrumbs from '../NavBreadcrumbs';

function defaultProps() {
  const entry = {
    uid: '123',
    name: 'test',
    status: 'passed',
    type: 'testplan',
    case_count: {
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
  let props;
  let mountedNavBreadcrumbs;
  const renderNavBreadcrumbs = () => {
    if (!mountedNavBreadcrumbs) {
      mountedNavBreadcrumbs = shallow(
        <NavBreadcrumbs {...props} />
      );
    }
    return mountedNavBreadcrumbs;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedNavBreadcrumbs = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.handleNavClick.mockClear();
  });

  it('shallow renders without crashing', () => {
    renderNavBreadcrumbs();
  });

  it('shallow renders the correct HTML structure', () => {
    const navBreadcrumbs = renderNavBreadcrumbs();
    expect(navBreadcrumbs).toMatchSnapshot();
  });

  it('calls handleNavClick when nav entry has been clicked', () => {
    const handleNavClick = props.handleNavClick;
    const navBreadcrumbs = renderNavBreadcrumbs();

    navBreadcrumbs.find('li').simulate('click');
    expect(handleNavClick.mock.calls.length).toEqual(1);
  })

});