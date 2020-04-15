/* Unit tests for the InteractiveNavEntry component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

import InteractiveNavEntry from '../InteractiveNavEntry';

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
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "running" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'running'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "passed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'passed'}
        runtime_status={'finished'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={9}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "failed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'failed'}
        runtime_status={'finished'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={8}
        caseCountFailed={1}
        handlePlayClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('calls handlePlayClick when the play button is clicked', () => {
    const handlePlayClick = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={handlePlayClick}
        envCtrlCallback={null}
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
        runtime_status={'finished'}
        envStatus={null}
        type={'testcase'}
        caseCountPassed={6}
        caseCountFailed={2}
        handlePlayClick={handlePlayClick}
        envCtrlCallback={null}
      />
    );

    renderedEntry.find(FontAwesomeIcon).simulate('click');
    expect(handlePlayClick.mock.calls.length).toEqual(1);
  });

  it('renders an entry with environment status STOPPED', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STOPPED'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders an entry with environment status STARTING', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STARTING'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders an entry with environment status STARTED', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STARTED'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders an entry with environment status STOPPING', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STOPPING'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('calls callback to start environment when toggle is clicked', () => {
    const envCtrlCallback = jest.fn()
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STOPPED'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(2);
    faIcons.find({title: 'Start environment'}).simulate('click');

    // The callback should have been called once when the component was
    // clicked, and it should have been called with a single arg of "start"
    // to start the environment.
    expect(envCtrlCallback.mock.calls).toHaveLength(1);
    expect(envCtrlCallback.mock.calls[0]).toHaveLength(2);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("start");
  });

  it('calls callback to stop environment when toggle is clicked', () => {
    const envCtrlCallback = jest.fn()
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={'FakeTestcase'}
        status={'unknown'}
        runtime_status={'ready'}
        envStatus={'STARTED'}
        type={'multitest'}
        caseCountPassed={0}
        caseCountFailed={0}
        handlePlayClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(2);
    faIcons.find({title: 'Start environment'}).simulate('click');

    // The callback should have been called once when the component was
    // clicked, and it should have been called with a single arg of "start"
    // to start the environment.
    expect(envCtrlCallback.mock.calls).toHaveLength(1);
    expect(envCtrlCallback.mock.calls[0]).toHaveLength(2);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("stop");
  });
});

