import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import FixLogAssertion from "../FixLogAssertion";

function defaultProps() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.314860+00:00",
      description: null,
      flattened_dict: [
        [0, 555, ""],
        [0, "", ""],
        [1, 624, ["int", "1"]],
        [1, 556, ["str", "USD"]],
        [0, "", ""],
        [1, 624, ["int", "2"]],
        [1, 556, ["str", "EUR"]],
        [0, 36, ["int", "6"]],
        [0, 38, ["int", "5"]],
        [0, 22, ["int", "5"]],
        [0, 55, ["int", "2"]],
      ],
      line_no: 688,
      meta_type: "entry",
      type: "FixLog",
      utc_time: "2019-02-12T17:41:43.314849+00:00",
    },
  };
}

describe("FixLogAssertion", () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it("shallow renders the correct HTML structure", () => {
    shallowComponent = shallow(<FixLogAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
