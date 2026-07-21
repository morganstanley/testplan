/* Unit tests for the InteractiveNavEntry component. */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StyleSheetTestUtils } from "aphrodite";
import { getDefaultStore } from "jotai";

import { pendingEnvRequestAtom } from "../../Report/InteractiveReport.js";
import InteractiveNavEntry from "../InteractiveNavEntry.js";

function defaultProps() {
  return {
    name: "FakeTestcase",
    description: "TestCaseDesc",
    envStatus: null,
    type: "testcase",
    caseCountPassed: 0,
    caseCountFailed: 0,
    handleClick: () => undefined,
    envCtrlCallback: null,
  };
}

describe("InteractiveNavEntry", () => {
  const props = defaultProps();

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
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "running" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"running"}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "resetting" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"resetting"}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "waiting" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"waiting"}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "passed" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"passed"}
        runtime_status={"finished"}
        caseCountPassed={9}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "failed" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"failed"}
        runtime_status={"finished"}
        caseCountPassed={8}
        caseCountFailed={1}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('renders a testcase in "not_run" state', () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"not_run"}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders the unstable counter when caseCountUnstable is non-zero", () => {
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"xfail"}
        runtime_status={"finished"}
        caseCountPassed={4}
        caseCountFailed={1}
        caseCountUnstable={3}
      />
    );
    const counter = getByTitle("passed/unstable/failed testcases");
    const numbers = Array.from(counter.querySelectorAll("span")).map(
      (s) => s.textContent
    );
    expect(numbers).toEqual(["4", "3", "1"]);
  });

  it("calls handleClick when the play button is clicked", () => {
    const handleClick = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        handleClick={handleClick}
      />
    );
    fireEvent.click(getByTitle("Run tests"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("calls handleClick when the replay button is clicked", () => {
    const handleClick = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"failed"}
        runtime_status={"finished"}
        caseCountPassed={6}
        caseCountFailed={2}
        handleClick={handleClick}
      />
    );
    fireEvent.click(getByTitle("Run tests"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders an entry with environment status STARTED", () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTED"}
        type={"multitest"}
        envCtrlCallback={() => undefined}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders an entry with environment status STARTING", () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTING"}
        type={"multitest"}
        envCtrlCallback={() => undefined}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders an entry with environment status STOPPED", () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        envCtrlCallback={() => undefined}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders an entry with environment status STOPPING", () => {
    const { asFragment } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPING"}
        type={"multitest"}
        envCtrlCallback={() => undefined}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it("calls callback to start environment when toggle is clicked", () => {
    const envCtrlCallback = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        envCtrlCallback={envCtrlCallback}
      />
    );
    fireEvent.click(getByTitle("Start environment"));

    expect(envCtrlCallback).toHaveBeenCalledTimes(1);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("start");
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STARTING");
  });

  it("calls callback to stop environment when toggle is clicked", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "");
    const envCtrlCallback = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTED"}
        type={"multitest"}
        envCtrlCallback={envCtrlCallback}
      />
    );
    fireEvent.click(getByTitle("Stop environment"));

    expect(envCtrlCallback).toHaveBeenCalledTimes(1);
    expect(envCtrlCallback.mock.calls[0][1]).toBe("stop");

    // The pending request should have been set
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STOPPING");
  });

  it("disables action when environment change request sent", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "STARTING");
    const envCtrlCallback = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STOPPED"}
        type={"multitest"}
        envCtrlCallback={envCtrlCallback}
      />
    );
    fireEvent.click(getByTitle("Pending action"));

    expect(envCtrlCallback).not.toHaveBeenCalled();
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("STARTING");
  });

  it("clears pending environment request when backend acknowledged", () => {
    getDefaultStore().set(pendingEnvRequestAtom, "STARTING");
    const envCtrlCallback = jest.fn();
    const { getByTitle } = render(
      <InteractiveNavEntry
        {...props}
        status={"unknown"}
        runtime_status={"ready"}
        envStatus={"STARTING"}
        type={"multitest"}
        envCtrlCallback={envCtrlCallback}
      />
    );
    fireEvent.click(getByTitle("Environment starting..."));

    expect(envCtrlCallback).not.toHaveBeenCalled();
    expect(getDefaultStore().get(pendingEnvRequestAtom)).toBe("");
  });
});
