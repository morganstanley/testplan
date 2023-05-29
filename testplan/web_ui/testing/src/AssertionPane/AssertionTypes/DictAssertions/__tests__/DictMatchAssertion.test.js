import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import DictMatchAssertion from "../DictMatchAssertion";

function defaultProps() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.295236+00:00",
      description: "Simple dict match",
      comparison: [
        [0, "foo", "Passed", ["int", "1"], ["int", "1"]],
        [0, "bar", "Failed", ["int", "2"], ["int", "5"]],
        [0, "baz", "Ignored", ["int", "2"], ["int", "5"]],
        [0, "extra-key", "Failed", [null, "ABSENT"], ["int", "10"]],
      ],
      line_no: 524,
      expected_description: null,
      actual_description: null,
      meta_type: "assertion",
      include_keys: null,
      passed: false,
      exclude_keys: ["baz"],
      type: "DictMatch",
      utc_time: "2019-02-12T17:41:43.295231+00:00",
    },
  };
}

describe("DictMatchAssertion", () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it("shallow renders the correct HTML structure", () => {
    shallowComponent = shallow(<DictMatchAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
