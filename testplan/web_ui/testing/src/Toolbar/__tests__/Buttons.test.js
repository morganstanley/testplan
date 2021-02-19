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
    const updateTimeDisplayCbk = jest.fn();
    const button = shallow(
      <TimeButton updateTimeDisplayCbk={updateTimeDisplayCbk} />
    );
    expect(button).toMatchSnapshot();
    button.find({title: "Display time information"}).simulate("click");
    expect(updateTimeDisplayCbk.mock.calls.length).toBe(1);
  });
});
