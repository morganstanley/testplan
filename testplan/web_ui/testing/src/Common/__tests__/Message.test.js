import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import Message from "../Message";

function defaultProps() {
  return {
    left: "1.5em",
    message: "test",
  };
}

describe("Message", () => {
  let props;
  let mountedMessage;
  const renderMessage = () => {
    if (!mountedMessage) {
      mountedMessage = shallow(<Message {...props} />);
    }
    return mountedMessage;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedMessage = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders without crashing", () => {
    renderMessage();
  });

  it("shallow renders the correct HTML structure", () => {
    const message = renderMessage();
    expect(message).toMatchSnapshot();
  });
});
