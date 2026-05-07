import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StyleSheetTestUtils } from "aphrodite";
import { MemoryRouter } from "react-router-dom";

import NavList from "../NavList";

function renderNavList(navListProps) {
  return render(
    <MemoryRouter>
      <NavList {...navListProps} />
    </MemoryRouter>
  );
}

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

  it("renders and matches snapshot", () => {
    const { asFragment } = renderNavList(props);
    expect(asFragment()).toMatchSnapshot();
  });

  it("renders xpass + xfail + skipped as the unstable counter for non-interactive entry", () => {
    const entry = {
      uid: "456",
      name: "test",
      description: "desc",
      status: "xfail",
      type: "testplan",
      counter: {
        passed: 1, failed: 1, xpass: 2, xfail: 3, skipped: 1, total: 8,
      },
      uids: ["456"],
    };
    const { getByTitle } = renderNavList({
      ...props,
      filter: null,
      entries: [entry],
    });
    const counter = getByTitle("passed/unstable/failed testcases");
    const numbers = Array.from(counter.querySelectorAll("span")).map(
      (s) => s.textContent
    );
    expect(numbers).toEqual(["1", "6", "1"]);
  });

  it("renders xpass + xfail + skipped as the unstable counter for interactive entry", () => {
    const entry = {
      uid: "789",
      name: "test",
      description: "desc",
      status: "xfail",
      runtime_status: "finished",
      type: "testplan",
      counter: {
        passed: 1, failed: 1, xpass: 2, xfail: 3, skipped: 1, total: 8,
      },
      uids: ["789"],
    };
    const { getByTitle } = renderNavList({
      ...props,
      filter: null,
      interactive: true,
      handleClick: () => undefined,
      envCtrlCallback: () => undefined,
      entries: [entry],
    });
    const counter = getByTitle("passed/unstable/failed testcases");
    const numbers = Array.from(counter.querySelectorAll("span")).map(
      (s) => s.textContent
    );
    expect(numbers).toEqual(["1", "6", "1"]);
  });

  it("includes xpass-strict in the failed counter", () => {
    const entry = {
      uid: "999",
      name: "test",
      description: "desc",
      status: "failed",
      type: "testplan",
      counter: {
        passed: 1, failed: 1, error: 1, "xpass-strict": 2, total: 5,
      },
      uids: ["999"],
    };
    const { getByTitle } = renderNavList({
      ...props,
      filter: null,
      entries: [entry],
    });
    const counter = getByTitle("passed/unstable/failed testcases");
    const numbers = Array.from(counter.querySelectorAll("span")).map(
      (s) => s.textContent
    );
    expect(numbers).toEqual(["1", "0", "4"]);
  });
});
