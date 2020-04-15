/* Unit tests for the InteractiveNav component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import InteractiveNav from '../InteractiveNav';
import FakeInteractiveReport from '../../__tests__/fixtures/FakeInteractiveReport';

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
        report={FakeInteractiveReport}
        selected={[FakeInteractiveReport]}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        handleNavClick={jest.fn()}
        handlePlayClick={jest.fn()}
        envCtrlCallback={jest.fn()}
      />
    );
    expect(renderedNav).toMatchSnapshot();
  });
});

