/**
 * Unit tests for the InteractiveButtons module
 */
import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import { ReloadButton, ResetButton, AbortButton, RunAllButton } from "../InteractiveButtons";

describe("ReloadButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const reloadCbk = jest.fn();
    const button = shallow(
      <ReloadButton reloadCbk={reloadCbk} reloading={false} />
    );
    expect(button).toMatchSnapshot();
    button.find({ title: "Reload code" }).simulate("click");
    expect(reloadCbk.mock.calls.length).toBe(1);
  });

  it("Renders a spinning icon when reload is in-progress", () => {
    const reloadCbk = jest.fn();
    const button = shallow(
      <ReloadButton reloadCbk={reloadCbk} reloading={true} />
    );
    expect(button).toMatchSnapshot();
  });
});

describe("ResetButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const resetCbk = jest.fn();
    const button = shallow(
      <ResetButton resetStateCbk={resetCbk} resetting={false} />
    );
    expect(button).toMatchSnapshot();
    button.find({ title: "Reset state" }).simulate("click");
    expect(resetCbk.mock.calls.length).toBe(1);
  });

  it("Renders a spinning icon when reset is in-progress", () => {
    const resetCbk = jest.fn();
    const button = shallow(
      <ResetButton resetStateCbk={resetCbk} resetting={true} />
    );
    expect(button).toMatchSnapshot();
  });
});

describe("AbortButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const abortCbk = jest.fn();
    const button = shallow(
      <AbortButton abortCbk={abortCbk} aborting={false} />
    );
    expect(button).toMatchSnapshot();
    button.find({ title: "Abort Testplan" }).simulate("click");
    expect(abortCbk.mock.calls.length).toBe(1);
  });

  it("Renders a spinning icon when abortion is in-progress", () => {
    const abortCbk = jest.fn();
    const button = shallow(<AbortButton abortCbk={abortCbk} aborting={true} />);
    expect(button).toMatchSnapshot();
  });
});

describe("RunAllButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const runAllCbk = jest.fn();
    const button = shallow(
      <RunAllButton runAllCbk={runAllCbk} running={false} />
    );
    expect(button).toMatchSnapshot();
    button.find({ title: "Run all tests" }).simulate("click");
    expect(runAllCbk.mock.calls.length).toBe(1);
  });

  it("Renders an inactive icon when running is in-progress", () => {
    const runAllCbk = jest.fn();
    const button = shallow(
      <RunAllButton runAllCbk={runAllCbk} running={true} />
    );
    expect(button).toMatchSnapshot();
  });
});
