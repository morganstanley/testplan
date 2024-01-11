/* Unit tests for the InteractiveNav component. */
import React from "react";
import { shallow, render } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import Nav from "../Nav.js";
import { FakeInteractiveReport } from "../../Common/sampleReports.js";
import { useTreeViewPreference } from "../../UserSettings/UserSettings.js";
import { getDefaultStore } from "jotai";

describe.each([
  { title: "List", useTreeView: false },
  { title: "TreeView", useTreeView: true },
])("Nav with $title", ({ useTreeView }) => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders and matches snapshot", () => {
    getDefaultStore().set(useTreeViewPreference, useTreeView);
    const renderedNav = shallow(
      <Nav
        interactive={true}
        report={FakeInteractiveReport}
        selected={[FakeInteractiveReport]}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
        handleNavClick={jest.fn()}
        handleClick={jest.fn()}
        envCtrlCallback={jest.fn()}
        pendingEnvRequest={""}
        setPendingEnvRequest={jest.fn()}
      />
    );
    expect(renderedNav).toMatchSnapshot();
  });
});
