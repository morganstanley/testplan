/**
 * Unit tests for the Buttons module
 */
import React from "react";
import {shallow} from "enzyme";
import {StyleSheetTestUtils} from "aphrodite";

import {TimeButton} from "../Buttons";

describe("TimeButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const toggleTimeDisplayCbk = jest.fn();
    const button = shallow(
      <TimeButton toggleTimeDisplayCbk={toggleTimeDisplayCbk} />
    );
    expect(button).toMatchSnapshot();
    button.find({title: "Toggle execution time"}).simulate("click");
    expect(toggleTimeDisplayCbk.mock.calls.length).toBe(1);
  });
});
