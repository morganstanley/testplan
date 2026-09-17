import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import FilterBox from "../FilterBox";
import ExtendedSearchDropdown from "../ExtendedSearchDropdown";

function defaultProps() {
  return {
    width: "19.5em",
    handleNavFilter: jest.fn(),
  };
}

describe("FilterBox", () => {
  let props;
  let mountedFilterBox;
  const renderFilterBox = () => {
    if (!mountedFilterBox) {
      mountedFilterBox = shallow(<FilterBox {...props} />);
    }
    return mountedFilterBox;
  };

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedFilterBox = undefined;
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    props.handleNavFilter.mockClear();
  });

  it("shallow renders without crashing", () => {
    renderFilterBox();
  });

  it("shallow renders the correct HTML structure", () => {
    const filterBox = renderFilterBox();
    expect(filterBox).toMatchSnapshot();
  });

  it(
    "calls handleNavFilter when text written to filter " + "for input box",
    () => {
      const handleNavFilter = props.handleNavFilter;
      const filterBox = renderFilterBox();

      filterBox
        .find("DebounceInput")
        .simulate("change", { target: { value: "Test" } });
      expect(handleNavFilter.mock.calls.length).toEqual(1);
    }
  );

  it("closes and resets extended search when the report changes", () => {
    props.report = { uid: "old-report" };
    props.onExtendedSearchNavigate = jest.fn();
    const filterBox = renderFilterBox();
    filterBox.setState({
      showExtendedSearch: true,
      extendedSearchState: {
        selectedTest: "test",
        selectedTestsuite: "suite",
        selectedTestcase: "case",
        selectedParams: { quantity: 1000 },
      },
    });

    filterBox.setProps({ report: { uid: "new-report" } });

    expect(filterBox.state("showExtendedSearch")).toBe(false);
    expect(filterBox.state("extendedSearchState")).toEqual({
      selectedTest: "",
      selectedTestsuite: "",
      selectedTestcase: "",
      selectedParams: {},
    });
  });

  it("shows extended search when navigation is available", () => {
    props.report = { uid: "new-report" };
    props.onExtendedSearchNavigate = jest.fn();
    const filterBox = renderFilterBox();

    expect(
      filterBox.find('[title="Extended Search - Search by parameters"]')
    ).toHaveLength(1);

    filterBox.setState({ showExtendedSearch: true });
    expect(filterBox.find(ExtendedSearchDropdown)).toHaveLength(1);
  });
});
