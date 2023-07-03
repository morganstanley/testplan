import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import XMLCheckAssertion from "../XMLCheckAssertion";

describe("XMLChekAssertion", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it("shallow renders", () => {
    const props = {
      assertion: {
        category: "DEFAULT",
        machine_time: "2019-02-12T17:41:43.321541+00:00",
        description: "Simple XML check for existence of xpath.",
        xpath: "/Root/Test",
        xml: "<Root>\n                <Test>Foo</Test>\n            </Root>\n",
        data: [],
        line_no: 710,
        tags: null,
        meta_type: "assertion",
        passed: true,
        message: "xpath: `/Root/Test` exists in the XML.",
        type: "XMLCheck",
        namespaces: null,
        utc_time: "2019-02-12T17:41:43.321534+00:00",
      },
    };
    const shallowComponent = shallow(<XMLCheckAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
