/* Unit tests for the InteractiveNavEntry component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

import InteractiveNavEntry from '../InteractiveNavEntry.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';

describe('InteractiveNavEntry', () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it('renders a testcase in "ready" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'ready'}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "running" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'running'}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "passed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'passed'}
        type={'testcase'}
        caseCountPassed={9}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "failed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'failed'}
        type={'testcase'}
        caseCountPassed={8}
        caseCountFailed={1}
        handlePlayClick={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('calls handlePlayClick when the play button is clicked', () => {
    const handlePlayClick = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'ready'}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={handlePlayClick}
      />
    );

    renderedEntry.find(FontAwesomeIcon).simulate('click');
    expect(handlePlayClick.mock.calls.length).toEqual(1);
  });

  it('calls handlePlayClick when the replay button is clicked', () => {
    const handlePlayClick = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'failed'}
        type={'testcase'}
        caseCountPassed={6}
        caseCountFailed={2}
        handlePlayClick={handlePlayClick}
      />
    );

    renderedEntry.find(FontAwesomeIcon).simulate('click');
    expect(handlePlayClick.mock.calls.length).toEqual(1);
  });
});

