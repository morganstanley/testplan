import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import NavBreadcrumbs from "../NavBreadcrumbs";

function defaultProps() {
  const entry = {
    uid: "123",
    name: "test",
    description: "desc",
    status: "passed",
    category: "testplan",
    counter: {
      passed: 0,
      failed: 0,
    },
    uids: ["123"],
  };
  return {
    entries: [entry],
    url: "/testplan/:uid/:selection*",
  };
}

describe("NavBreadcrumbs", () => {
  const props = defaultProps();

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders the correct HTML structure", () => {
    const navBreadcrumbs = shallow(<NavBreadcrumbs {...props} />);
    expect(navBreadcrumbs).toMatchSnapshot();
  });
});
