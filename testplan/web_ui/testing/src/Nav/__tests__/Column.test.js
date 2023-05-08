import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import Column from "../Column";

describe("Column", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders the correct HTML structure", () => {
    const column = shallow(
      <Column width={"20em"}>
        <p className="unique" />
      </Column>
    );
    expect(column).toMatchSnapshot();
  });
});
