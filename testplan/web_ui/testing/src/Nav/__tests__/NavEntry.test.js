import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { getDefaultStore } from "jotai";

import NavEntry from "../NavEntry";
import { showStatusIconsPreference } from "../../UserSettings/UserSettings";

function defaultProps() {
  return {
    name: "entry name",
    description: "entry description",
    status: "passed",
    type: "testplan",
    caseCountPassed: 0,
    caseCountFailed: 0,
  };
}

describe("NavEntry", () => {
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
    const navEntry = shallow(<NavEntry {...props} />);
    expect(navEntry).toMatchSnapshot();
  });

  it('when prop status="failed" name div and Badge have correct styles', () => {
    const failProps = { ...props, status: "failed" };
    const navEntry = shallow(<NavEntry {...failProps} />);
    expect(navEntry).toMatchSnapshot();
  });

  it('when prop status="xfail" name div and Badge have correct styles', () => {
    const failProps = { ...props, status: "xfail" };
    const navEntry = shallow(<NavEntry {...failProps} />);
    expect(navEntry).toMatchSnapshot();
  });

  it("shallow renders the correct HTML structure with status icons enabled", () => {
    getDefaultStore().set(showStatusIconsPreference, true);
    const navEntry = shallow(<NavEntry {...props} />);
    expect(navEntry).toMatchSnapshot();
  });
});
