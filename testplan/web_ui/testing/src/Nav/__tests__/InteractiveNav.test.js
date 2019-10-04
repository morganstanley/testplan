/* Unit tests for the InteractiveNav component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import InteractiveNav from '../InteractiveNav.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';

describe('InteractiveNav', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('shallow renders and matches snapshot', () => {
    const renderedNav = shallow(
      <InteractiveNav
        report={[FakeInteractiveReport]}
        saveAssertions={() => undefined}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        runEntry={() => undefined}
      />
    );
    expect(renderedNav).toMatchSnapshot();
  });
});

