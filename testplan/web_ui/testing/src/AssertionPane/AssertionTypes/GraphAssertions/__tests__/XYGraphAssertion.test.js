import React from "react";
import { render, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import XYGraphAssertion from "../XYGraphAssertion.js";

function defaultProps() {
  return {
    assertion: {
      meta_type: "entry",
      utc_time: "2019-07-12T12:36:09.782759+00:00",
      machine_time: "2019-07-12T12:36:09.782759+00:00",
      type: "Graph",
      series_options: {
        "Data Name": { colour: "red" },
      },
      line_no: 50,
      graph_data: {
        "Data Name": [
          { x: "A", y: 10 },
          { x: "B", y: 5 },
          { x: "C", y: 15 },
        ],
      },
      description: "Bar Graph",
      category: "DEFAULT",
      graph_options: { legend: true },
      graph_type: "Bar",
    },
  };
}

describe("XYGraphAssertion", () => {
  let props;

  beforeEach(() => {
    props = defaultProps();
  });

  it("renders the correct HTML structure", () => {
    const component = render(<XYGraphAssertion {...props} />);
    expect(component.asFragment()).toMatchSnapshot();
  });

  it("renders a canvas for Line graphs", () => {
    props.assertion.graph_type = "Line";
    props.assertion.graph_data = {
      "Data Name": [
        { x: 0, y: 8 },
        { x: 1, y: 5 },
      ],
    };
    const component = render(<XYGraphAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toBeInTheDocument();
  });

  it("renders a canvas for Scatter graphs", () => {
    props.assertion.graph_type = "Scatter";
    const component = render(<XYGraphAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toBeInTheDocument();
  });

  it("renders a canvas for multi-series Bar graphs with different categories", () => {
    props.assertion.graph_data = {
      "Bar 1": [
        { x: "A", y: 10 },
        { x: "B", y: 5 },
        { x: "C", y: 15 },
      ],
      "Bar 2": [
        { x: "A", y: 3 },
        { x: "B", y: 6 },
        { x: "C", y: 15 },
        { x: "D", y: 12 },
      ],
    };
    props.assertion.series_options = {
      "Bar 1": { colour: "green" },
      "Bar 2": { colour: "purple" },
    };
    const component = render(<XYGraphAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toBeInTheDocument();
  });

  it("resets zoom without throwing on double click", () => {
    const component = render(<XYGraphAssertion {...props} />);
    const chartContainer = component.container.querySelector("canvas")
      .parentElement;
    expect(() => fireEvent.doubleClick(chartContainer)).not.toThrow();
  });

  it("renders a fallback message for a removed graph type", () => {
    props.assertion.graph_type = "Whisker";
    const component = render(<XYGraphAssertion {...props} />);
    expect(component.container.querySelector("canvas")).not.toBeInTheDocument();
    expect(component.getByText(/removed/)).toBeInTheDocument();
  });
});
