import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";

import TimelineAssertion from "../TimelineAssertion";

function defaultProps() {
  return {
    assertion: {
      type: "Timeline",
      meta_type: "entry",
      timeline_data: {
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

describe("TimelineAssertion", () => {
  let props;

  beforeEach(() => {
    props = defaultProps();
  });

  it("renders the correct HTML structure", () => {
    const component = render(<TimelineAssertion {...props} />);
    expect(component.asFragment()).toMatchSnapshot();
  });

  it("sizes the chart based on the number of rows", () => {
    const component = render(<TimelineAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toHaveAttribute(
      "height",
      "20"
    );
  });

  it("renders without rows", () => {
    props.assertion.timeline_data = { Drivers: [] };
    const component = render(<TimelineAssertion {...props} />);
    expect(component.container.querySelector("canvas")).toHaveAttribute(
      "height",
      "10"
    );
  });
});
