import React from "react";
import { ListGroupItem } from "reactstrap";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import NavList from "../NavList";

function defaultProps() {
  const entry = {
    uid: "123",
    name: "test",
    description: "desc",
    status: "passed",
    type: "testplan",
    counter: {
      passed: 1,
      failed: 0,
    },
    uids: ["123"],
  };
  return {
    entries: [entry],
    breadcrumbLength: 1,
    width: "22em",
    filter: "all",
    displayEmpty: true,
    displayTags: true,
    displayTime: false,
    url: "/testplan/:uid/:selection*",
  };
}

describe("NavList", () => {
  const props = defaultProps();

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders and matches snapshot", () => {
    const nav_list = shallow(<NavList {...props} />);
    expect(nav_list).toMatchSnapshot();
  });
});
