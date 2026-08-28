import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";

import DiscreteChartAssertion from "../DiscreteChartAssertion.js";

function defaultProps() {
  return {
    assertion: {
      meta_type: "entry",
      utc_time: "2019-07-12T12:36:09.796381+00:00",
      machine_time: "2019-07-12T12:36:09.796381+00:00",
      type: "DiscreteChart",
      series_options: {
        "Data Name": {
          colour: "literal",
        },
      },
      line_no: 101,
      graph_data: {
        "Data Name": [
          {
            angle: 1,
            color: "#89DAC1",
            name: "green",
          },
          {
            angle: 2,
            color: "#F6D18A",
            name: "yellow",
          },
          {
            angle: 5,
            color: "#1E96BE",
            name: "cyan",
          },
          {
            angle: 3,
            color: "#DA70BF",
            name: "magenta",
          },
          {
            angle: 5,
            color: "#F6D18A",
            name: "yellow again",
          },
        ],
      },
      description: "Pie Chart",
      category: "DEFAULT",
      graph_options: null,
      graph_type: "Pie",
    },
  };
}

describe("DiscreteChartAssertion", () => {
  let props;

  beforeEach(() => {
    props = defaultProps();
  });

  it("renders the correct HTML structure", () => {
    const component = render(<DiscreteChartAssertion {...props} />);
    expect(component.asFragment()).toMatchSnapshot();
  });

  it("renders one canvas per series", () => {
    props.assertion.graph_data = {
      "Series A": props.assertion.graph_data["Data Name"],
      "Series B": props.assertion.graph_data["Data Name"],
    };
    props.assertion.series_options = {
      "Series A": { colour: "literal" },
      "Series B": { colour: "red" },
    };
    const component = render(<DiscreteChartAssertion {...props} />);
    expect(component.container.querySelectorAll("canvas")).toHaveLength(2);
  });
});
