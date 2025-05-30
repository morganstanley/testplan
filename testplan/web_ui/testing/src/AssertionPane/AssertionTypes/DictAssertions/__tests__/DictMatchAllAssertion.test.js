import React from "react";
import { render } from "@testing-library/react";
import { StyleSheetTestUtils } from "aphrodite";

import DictMatchAllAssertion from "../DictMatchAllAssertion";

function defaultProps() {
  return {
    assertion: {
      category: "DEFAULT",
      description: "Simple dict match all",
      key_weightings: null,
      matches: [
        {
          description: "Simple dict match all 1/3: expected[2] vs values[0]",
          comparison: [
            ["foo", "p", ["int", 2], ["int", 2]],
            ["bar", "p", ["int", 5], ["int", 5]]
          ],
          passed: true,
          comparison_index: 2
        },
        {
          description: "Simple dict match all 2/3: expected[0] vs values[1]",
          comparison: [
            ["foo", "p", ["int", 1], ["int", 1]],
            ["bux", "f", ["int", 99], ["int", 98]]
          ],
          passed: false,
          comparison_index: 0
        },
        {
          description: "Simple dict match all 3/3: expected[1] vs values[2]",
          comparison: [
            ["foo", "p", ["int", 3], ["int", 3]],
            ["bar", "p", ["int", 0], ["int", 0]]
          ],
          passed: true,
          comparison_index: 1
        }
      ],
      meta_type: "assertion",
      passed: false,
      timestamp: 1747749737.578596,
      type: "DictMatchAll"
    },
  };
}

describe("DictMatchAllAssertion", () => {
  let component;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it("renders the correct HTML structure", () => {
    component = render(<DictMatchAllAssertion {...defaultProps()} />);
    expect(component.asFragment()).toMatchSnapshot();
  });
});