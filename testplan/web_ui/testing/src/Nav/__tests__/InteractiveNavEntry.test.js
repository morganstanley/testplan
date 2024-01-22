/* Unit tests for the InteractiveNavEntry component. */
import React from "react";
import { render, shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useAtom, getDefaultStore } from "jotai";

import { pendingEnvRequestAtom } from "../../Report/InteractiveReport.js";
import InteractiveNavEntry from "../InteractiveNavEntry.js";

describe("InteractiveNavEntry", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    // Make sure the pendingEnvRequestAtom is set to default value
    getDefaultStore().set(pendingEnvRequestAtom, "");
  });

  it('renders a testcase in "ready" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "running" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"running"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "resetting" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"resetting"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "waiting" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"waiting"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "passed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"passed"}
        runtime_status={"finished"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={9}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "failed" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"failed"}
        runtime_status={"finished"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={8}
        caseCountFailed={1}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it('renders a testcase in "not_run" state', () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"not_run"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={null}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it("calls handleClick when the play button is clicked", () => {
    const handleClick = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={handleClick}
        envCtrlCallback={null}
      />
    );

    renderedEntry.find(FontAwesomeIcon).simulate("click");
    expect(handleClick.mock.calls.length).toEqual(1);
  });

  it("calls handleClick when the replay button is clicked", () => {
    const handleClick = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"failed"}
        runtime_status={"finished"}
        envStatus={null}
        type={"testcase"}
        caseCountPassed={6}
        caseCountFailed={2}
        handleClick={handleClick}
        envCtrlCallback={null}
      />
    );

    renderedEntry.find(FontAwesomeIcon).simulate("click");
    expect(handleClick.mock.calls.length).toEqual(1);
  });

  it("renders an entry with environment status STARTED", () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTED"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it("renders an entry with environment status STARTING", () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTING"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it("renders an entry with environment status STOPPED", () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it("renders an entry with environment status STOPPING", () => {
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPING"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={() => undefined}
      />
    );
    expect(renderedEntry).toMatchSnapshot();
  });

  it("calls callback to start environment when toggle is clicked", () => {
    const envCtrlCallback = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(3);
    faIcons.find({ title: "Start environment" }).simulate("click");

    // The callback should have been called once when the component was
    // clicked, and it should have been called with a single arg of "start"
    // to start the environment.
    expect(envCtrlCallback.mock.calls).toHaveLength(1);
    expect(envCtrlCallback.mock.calls[0]).toHaveLength(2);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("start");

    // The pending request should have been set.
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STARTING");
  });

  it("calls callback to stop environment when toggle is clicked", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "");
    const envCtrlCallback = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTED"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(3);
    console.log(faIcons);
    faIcons.find({ title: "Stop environment" }).simulate("click");

    // The callback should have been called once when the component was
    // clicked, and it should have been called with a single arg of "start"
    // to start the environment.
    expect(envCtrlCallback.mock.calls).toHaveLength(1);
    expect(envCtrlCallback.mock.calls[0]).toHaveLength(2);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("stop");

    // The pending request should have been set
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STOPPING");
  });

  it("disables action when environment change request sent", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "STARTING");
    const envCtrlCallback = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(3);
    faIcons.find({ title: "Pending action" }).simulate("click", {
      preventDefault: () => {},
      stopPropagation: () => {}
    });

    // The callback should not have been called.
    expect(envCtrlCallback.mock.calls).toHaveLength(0);

    // The pending env request should not have been changed.
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STARTING");
  });

  it("clears pending environment request when backend acknowledged", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "STARTING");
    const envCtrlCallback = jest.fn();
    const renderedEntry = shallow(
      <InteractiveNavEntry
        name={"FakeTestcase"}
        description={"TestCaseDesc"}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTING"}
        type={"multitest"}
        caseCountPassed={0}
        caseCountFailed={0}
        handleClick={() => undefined}
        envCtrlCallback={envCtrlCallback}
      />
    );

    // Find the environment control. Since there are two FontAwesomeIcons,
    // we need to additionally filter for the one which is the environment
    // controller - we do this by matching on the title text.
    const faIcons = renderedEntry.find(FontAwesomeIcon);
    expect(faIcons).toHaveLength(3);
    faIcons.find({ title: "Environment starting..." }).simulate("click", {
      preventDefault: () => {},
      stopPropagation: () => {}
    });
    
    // The callback should not have been called.
    expect(envCtrlCallback.mock.calls).toHaveLength(0);

    // The pending request should have been cleared.
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("");
  });
});
