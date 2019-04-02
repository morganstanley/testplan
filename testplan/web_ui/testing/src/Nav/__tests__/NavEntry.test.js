import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import {Badge} from 'reactstrap';

import NavEntry from '../NavEntry';

function defaultProps() {
  return {
    name: 'entry name',
    status: 'passed',
    type: 'testplan',
    caseCountPassed: 0,
    caseCountFailed: 0,
  };
}

describe('NavEntry', () => {
  let props;
  let mountedNavEntry;
  const renderNavEntry = () => {
    if (!mountedNavEntry) {
      mountedNavEntry = shallow(
        <NavEntry {...props} />
      );
    }
    return mountedNavEntry;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedNavEntry = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('shallow renders without crashing', () => {
    renderNavEntry();
  });

  it('shallow renders the correct HTML structure', () => {
    const navEntry = renderNavEntry();
    expect(navEntry).toMatchSnapshot();
  });

  it('when prop status="failed" name div and Badge have correct styles', () => {
    props.status = 'failed';
    const navEntry = renderNavEntry();

    const name = navEntry.children().first();
    expect(name).toHaveLength(1);
    const expectedName = defaultProps().name;
    expect(name.text()).toEqual(expectedName);
    expect(name.props().className).toMatch(/failed/);

    const badge = navEntry.find(Badge);
    expect(badge).toHaveLength(1);
    expect(badge.props().className).toMatch(/failedBadge/);
  });
});