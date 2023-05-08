import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import CodeLogAssertion from "../CodeLogAssertion";

function defaultProps() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.302500+00:00",
      description: null,
      language: "c",
      code: '#include <stdio.h>\nint main()\n{\n    printf("Hello world!")\n    return 0;\n}\n',
      line_no: 123,
      meta_type: "entry",
      type: "CodeLog",
      utc_time: "2019-02-12T17:41:43.302494+00:00",
    },
  };
}

describe("CodeLogAssertion", () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it("shallow renders the correct HTML structure", () => {
    shallowComponent = shallow(<CodeLogAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
