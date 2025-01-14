import React from "react";
import { render } from "@testing-library/react";
import { StyleSheetTestUtils } from "aphrodite";

import AssertionHeader from "../AssertionHeader";

const props = {
  assertion: {
    utc_time: "2024-12-24T09:35:56.113946+00:00",
    machine_time: "2024-12-24T17:35:56.113951+08:00",
    type: "Equal",
    meta_type: "assertion",
    description: "soda water == soda water",
    line_no: 26,
    category: "DEFAULT",
    flag: "DEFAULT",
    file_path: "/dummy/examples/Driver/Dependency/suites.py",
    passed: true,
    first: "soda water",
    second: "soda water",
    label: "==",
    type_actual: "str",
    type_expected: "str",
  },
  displayPath: false,
  uid: "c260c2af-888a-4853-86b2-82a14f44066e", // generated
  toggleExpand: jest.fn(),
  showStatusIcons: false,
};

describe("AssertionHeader", () => {
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    shallowComponent = undefined;
  });

  it("shallow renders the correct HTML structure", () => {
    shallowComponent = render(<AssertionHeader {...props} />);
    expect(
      shallowComponent.getByText(props.assertion.description)
    ).toBeDefined();
    expect(shallowComponent.baseElement).toMatchSnapshot();
  });

  it("shallow renders the correct HTML structure with status icons enabled", () => {
    shallowComponent = render(
      <AssertionHeader {...{ ...props, showStatusIcons: true }} />
    );
    expect(shallowComponent.container.querySelector("svg")).not.toBeNull();
    expect(shallowComponent.baseElement).toMatchSnapshot();
  });

  it("shallow renders the correct HTML structure with code context enabled", () => {
    shallowComponent = render(
      <AssertionHeader {...{ ...props, displayPath: true }} />
    );
    expect(
      shallowComponent.getByText(props.assertion.file_path, { exact: false })
    ).toBeDefined();
    expect(shallowComponent.baseElement).toMatchSnapshot();
  });
});
