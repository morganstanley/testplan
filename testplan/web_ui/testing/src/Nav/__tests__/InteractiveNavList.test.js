/* Unit tests for the InteractiveNavList component. */
import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import NavList from "../NavList.js";
import { FakeInteractiveReport } from "../../Common/sampleReports.js";
import { PropagateIndices } from "../../Report/reportUtils.js";

describe("InteractiveNavList", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders and matches snapshot", () => {
    const entries = PropagateIndices(FakeInteractiveReport).entries;
    const renderedNavList = shallow(
      <NavList
        interactive={true}
        entries={entries}
        breadcrumbLength={1}
        width={"28em"}
        handleNavClick={() => undefined}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
        handleClick={(e, action) => undefined}
        envCtrlCallback={(e, action) => undefined}
      />
    );
    expect(renderedNavList).toMatchSnapshot();
  });
});
