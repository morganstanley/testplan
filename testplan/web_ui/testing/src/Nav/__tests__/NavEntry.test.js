import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
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

  it("renders the correct HTML structure", () => {
    const { asFragment } = render(<NavEntry {...props} />);
    expect(asFragment()).toMatchSnapshot();
  });

  it('when prop status="failed" name div and Badge have correct styles', () => {
    const failProps = { ...props, status: "failed" };
    const { asFragment } = render(<NavEntry {...failProps} />);
    expect(asFragment()).toMatchSnapshot();
  });

  it('when prop status="xfail" name div and Badge have correct styles', () => {
    const failProps = { ...props, status: "xfail" };
    const { asFragment } = render(<NavEntry {...failProps} />);
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders the unstable counter when caseCountUnstable is non-zero", () => {
    const unstableProps = {
      ...props,
      status: "xfail",
      caseCountPassed: 4,
      caseCountFailed: 1,
      caseCountUnstable: 3,
    };
    const { getByTitle } = render(<NavEntry {...unstableProps} />);
    const counter = getByTitle("passed/unstable/failed testcases");
    const numbers = Array.from(counter.querySelectorAll("span")).map(
      (s) => s.textContent
    );
    expect(numbers).toEqual(["4", "3", "1"]);
  });

  it("renders the correct HTML structure with status icons enabled", () => {
    getDefaultStore().set(showStatusIconsPreference, true);
    const { asFragment } = render(<NavEntry {...props} />);
    expect(asFragment()).toMatchSnapshot();
  });
});
