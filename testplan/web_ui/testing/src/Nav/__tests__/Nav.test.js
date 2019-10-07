import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import Nav from '../Nav';
import {TESTPLAN_REPORT} from '../../Common/sampleReports';

function defaultProps() {
  return {
    report: TESTPLAN_REPORT,
    saveAssertions: jest.fn(),
  };
}

describe('Nav', () => {
  let props;
  let mountedNav;
  const renderNav = () => {
    if (!mountedNav) {
      mountedNav = shallow(
        <Nav {...props} />
      );
    }
    return mountedNav;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedNav = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.saveAssertions.mockClear();
  });

  it('shallow renders without crashing', () => {
    renderNav();
  });

  it('shallow renders the correct HTML structure', () => {
    const nav = renderNav();
    expect(nav).toMatchSnapshot();
  });

  // Unsure how to test handleNavClick. Already checked it is called
  // in correct place in child components. Should we call it and check
  // state is changed correctly? Not sure we should be testing state
  // change, as this is an input/internal implementation detail not an
  // output of the react component.

  // Unsure how to test autoSelect. Already checked it is called
  // in correct place in child components. Should we call it and check
  // state is changed correctly? Not sure we should be testing state
  // change, as this is an input/internal implementation detail not an
  // output of the react component.

});
