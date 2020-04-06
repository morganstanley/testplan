/* Unit tests for the InteractiveNavList component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import InteractiveNavList from '../InteractiveNavList.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';

describe('InteractiveNavList', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('shallow renders and matches snapshot', () => {
    const renderedNavList = shallow(
      <InteractiveNavList
        entries={FakeInteractiveReport.entries}
        breadcrumbLength={1}
        handleNavClick={() => undefined}
        autoSelect={() => undefined}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
        handlePlayClick={(e) => undefined}
        envCtrlCallback={(e, action) => undefined}
      />
    );
    expect(renderedNavList).toMatchSnapshot();
  });
});

