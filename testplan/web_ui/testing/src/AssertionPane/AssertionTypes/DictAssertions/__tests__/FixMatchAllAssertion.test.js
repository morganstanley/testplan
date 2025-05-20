import React from "react";
import { render } from "@testing-library/react";
import { StyleSheetTestUtils } from "aphrodite";

import DictMatchAllAssertion from "../DictMatchAllAssertion";

function defaultProps() {
  return {
    assertion: {
      category: "DEFAULT",
      description: "fix match all",
      key_weightings: null,
      matches: [
        {
          description: "fix match all 1/2: expected[1] vs values[0]",
          comparison: [
            [10914, "p", ["str", "c1dec2c5"], ["str", "c1dec2c5"]],
            [38, "p", ["str", "500"], ["str", "500"]],
            [44, "p", ["float", 9.0], ["str", "9"]]
          ],
          passed: true,
          comparison_index: 1
        },
        {
          description: "fix match all 2/2: expected[0] vs values[1]",
          comparison: [
            [10914, "p", ["REGEX", ".+"], ["str", "f3ea6276"]],
            [38, "p", ["int", 501], ["int", 501]],
            [44, "p", ["float", 9.1], ["float", 9.1]]
          ],
          passed: true,
          comparison_index: 0
        }
      ],
      meta_type: "assertion",
      passed: true,
      timestamp: 1747749737.592704,
      type: "FixMatchAll"
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