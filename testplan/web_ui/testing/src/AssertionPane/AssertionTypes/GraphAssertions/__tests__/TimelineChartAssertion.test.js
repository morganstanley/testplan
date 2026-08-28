import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";

import TimelineChartAssertion from "../TimelineChartAssertion.js";

function defaultProps() {
  return {
    assertion: {
      type: "Graph",
      meta_type: "entry",
      graph_type: "Timeline",
      series_options: null,
      graph_options: null,
      graph_data: {
        Drivers: [
          {
            name: "server",
            start: "2024-01-01T00:00:00+00:00",
            end: "2024-01-01T00:00:01+00:00",
          },
          {
            name: "client",
            start: "2024-01-01T00:00:00.500000+00:00",
            end: "2024-01-01T00:00:01.500000+00:00",
          },
        ],
      },
      description: "Driver Setup Timeline",
    },
  };
}

describe("TimelineChartAssertion", () => {
  let props;

  beforeEach(() => {
    props = defaultProps();
  });

  it("renders the correct HTML structure", () => {
    const component = render(<TimelineChartAssertion {...props} />);
    expect(component.asFragment()).toMatchSnapshot();
  });

  it("sizes the chart based on the number of rows", () => {
    const component = render(<TimelineChartAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toHaveAttribute(
      "height",
      "20"
    );
  });

  it("renders without rows", () => {
    props.assertion.graph_data = { Drivers: [] };
    const component = render(<TimelineChartAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toHaveAttribute(
      "height",
      "10"
    );
  });

  it("renders a canvas for multi-series data with distinct series colours", () => {
    props.assertion.graph_data = {
      Drivers: [
        {
          name: "server",
          start: "2024-01-01T00:00:00+00:00",
          end: "2024-01-01T00:00:01+00:00",
        },
      ],
      Workers: [
        {
          name: "worker",
          start: "2024-01-01T00:00:01+00:00",
          end: "2024-01-01T00:00:03+00:00",
        },
      ],
    };
    props.assertion.series_options = {
      Drivers: { colour: "red" },
      Workers: { colour: "blue" },
    };
    const component = render(<TimelineChartAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toBeInTheDocument();
  });
});
