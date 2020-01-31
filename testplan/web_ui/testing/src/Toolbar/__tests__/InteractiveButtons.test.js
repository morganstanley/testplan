/**
 * Unit tests for the InteractiveButtons module
 */
import React from "react";
import {shallow} from "enzyme";
import {StyleSheetTestUtils} from "aphrodite";

import {ResetButton} from "../InteractiveButtons";

describe("ResetButton", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("Renders a clickable button", () => {
    const resetCbk = jest.fn();
    const button = shallow(
      <ResetButton resetStateCbk={resetCbk} resetting={false} />
    );
    expect(button).toMatchSnapshot();
    button.find({title: "Reset state"}).simulate("click");
    expect(resetCbk.mock.calls.length).toBe(1);
  });

  it("Renders a spinning icon when reset is in-progress", () => {
    const resetCbk = jest.fn();
    const button = shallow(
      <ResetButton resetStateCbk={resetCbk} resetting={true} />
    );
    expect(button).toMatchSnapshot();
  });

});
