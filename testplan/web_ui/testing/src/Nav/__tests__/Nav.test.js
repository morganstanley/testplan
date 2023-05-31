import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import Nav from "../Nav";
import { TESTPLAN_REPORT } from "../../Common/sampleReports";
import { getDefaultStore } from "jotai";
import { useTreeViewPreference } from "../../UserSettings/UserSettings";

const defaultProps = {
  report: TESTPLAN_REPORT,
  selected: [TESTPLAN_REPORT],
};

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
    const rendered = shallow(<Nav {...defaultProps} />);
    expect(rendered).toMatchSnapshot();
  });
});
