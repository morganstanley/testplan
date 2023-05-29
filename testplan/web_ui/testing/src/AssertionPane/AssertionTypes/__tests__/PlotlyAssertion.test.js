import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import PlotlyAssertion from "../PlotlyAssertion";

function defaultProps() {
  return {
    assertion: {
      type: "Plotly",
      meta_type: "entry",
      utc_time: "2021-06-03T08:31:16.613418+00:00",
      category: "DEFAULT",
      flag: "DEFAULT",
      hash: "f97c8d4c90fccc79e6921ba62583c7ad99b71561",
      filesize: 7813,
      source_path: "1f8037cf-ec3e-48e2-8329-d2910ad04ca6.json",
      style: null,
      machine_time: "2021-06-03T16:31:16.613430+00:00",
      orig_filename: "1f8037cf-ec3e-48e2-8329-d2910ad04ca6.json",
      dst_path:
        "1f8037cf-ec3e-48e2-8329-d2910ad04ca6-f97c8d4c90fccc79e6921ba62583c7ad99b71561-7813.json",
      line_no: 71,
      description: "Task",
    },
  };
}

describe("PlotlyAssertion", () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it("shallow renders the correct HTML structure", () => {
    shallowComponent = shallow(<PlotlyAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
