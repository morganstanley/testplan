import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { COLUMN_WIDTH } from "../../Common/defaults";

import Toolbar from "../Toolbar";
import {
  TOOLBAR_BUTTONS_BATCH,
  TOOLBAR_BUTTONS_INTERACTIVE,
} from "../../Common/defaults";
import { ReloadButton, ResetButton, AbortButton } from "../InteractiveButtons";

function defaultProps() {
  return {
    status: "passed",
    buttons: TOOLBAR_BUTTONS_BATCH,
    handleNavFilter: jest.fn(),
    filterBoxWidth: `${COLUMN_WIDTH}em`,
  };
}

describe("Toolbar", () => {
  let props;
  let mountedToolbar;
  const renderToolbar = () => {
    if (!mountedToolbar) {
      mountedToolbar = shallow(<Toolbar {...props} />);
    }
    return mountedToolbar;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedToolbar = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.handleNavFilter.mockClear();
  });

  it("shallow renders without crashing", () => {
    renderToolbar();
  });

  it("shallow renders the correct HTML structure for batch mode", () => {
    const toolbar = renderToolbar();
    expect(toolbar).toMatchSnapshot();
  });

  it("shallow renders the correct HTML structure for interactive mode", () => {
    props.buttons = TOOLBAR_BUTTONS_INTERACTIVE;
    const toolbar = renderToolbar();
    expect(toolbar).toMatchSnapshot();
  });

  it("uses the failed style when status is failed", () => {
    props.status = "failed";
    const toolbar = renderToolbar();
    const container = toolbar.find("Collapse").get(0);
    expect(container.props.className).toMatch(/toolbar.+toolbarFailed/);
  });

  it("uses the neutral style when status is unknown", () => {
    props.status = "unknown";
    const toolbar = renderToolbar();
    const container = toolbar.find("Collapse").get(0);
    expect(container.props.className).toMatch(/toolbar.+toolbarUnknown/);
  });

  it("inserts extra buttons into the toolbar", () => {
    const resetCbk = jest.fn();
    props.extraButtons = [
      ReloadButton({ reloading: false, reloadCbk: jest.fn() }),
      ResetButton({ resetting: false, resetStateCbk: jest.fn() }),
      AbortButton({ aborting: false, abortCbk: jest.fn() }),
    ];
    const toolbar = renderToolbar();
    expect(toolbar).toMatchSnapshot();
  });
});
