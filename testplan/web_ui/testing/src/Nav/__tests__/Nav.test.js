import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import Nav from "../Nav";
import { TESTPLAN_REPORT } from "../../Common/sampleReports";

const defaultProps = {
  report: TESTPLAN_REPORT,
  selected: [TESTPLAN_REPORT],
};

describe("Nav", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders and matches snapshot", () => {
    const rendered = shallow(<Nav {...defaultProps} />);
    expect(rendered).toMatchSnapshot();
  });
});
