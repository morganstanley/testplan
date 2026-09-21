import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { fireEvent, render } from "@testing-library/react";

import { filterEntries } from "../../Report/reportFilter";
import { PropagateIndices } from "../../Report/reportUtils";
import ExtendedSearchDropdown, {
  collectTestcases,
  paramValueToken,
  buildFilterOptions,
  applyParamFilters,
} from "../ExtendedSearchDropdown";

function defaultProps() {
  return {
    report: {
      uid: "report-1",
      entries: [
        {
          category: "multitest",
          name: "MyTest",
          uid: "mt1",
          entries: [
            {
              category: "testsuite",
              name: "MySuite",
              uid: "ts1",
              entries: [
                {
                  category: "testcase",
                  name: "case1",
                  uid: "tc1",
                  uids: ["report-1", "mt1", "ts1", "tc1"],
                },
              ],
            },
          ],
        },
      ],
    },
    onNavigate: jest.fn(),
    onClose: jest.fn(),
    handleNavFilter: jest.fn(),
    value: {
      selectedTest: "",
      selectedTestsuite: "",
      selectedTestcase: "",
      selectedParams: {},
      searchText: "",
    },
    onStateChange: jest.fn(),
  };
}

function parametrizedReport(version, testcaseEntries) {
  const reportUid = `report-v${version}`;
  return {
    version,
    uid: reportUid,
    entries: [
      {
        category: "multitest",
        name: "MyTest",
        uid: "mt1",
        entries: [
          {
            category: "testsuite",
            name: "MySuite",
            uid: "ts1",
            entries: [
              {
                category: "parametrization",
                name: "test_order",
                uid: "test_order",
                entries: testcaseEntries.map((entry) => ({
                  ...entry,
                  uids: [reportUid, "mt1", "ts1", "test_order", entry.uid],
                })),
              },
            ],
          },
        ],
      },
    ],
  };
}

describe("ExtendedSearchDropdown", () => {
  let props;
  let mountedDropdown;
  const renderDropdown = () => {
    if (!mountedDropdown) {
      mountedDropdown = shallow(<ExtendedSearchDropdown {...props} />);
    }
    return mountedDropdown;
  };

  beforeEach(() => {
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    mountedDropdown = undefined;
    props.onStateChange.mockImplementation((patch) => {
      props.value = { ...props.value, ...patch };
      if (mountedDropdown) {
        mountedDropdown.setProps({ value: props.value });
      }
    });
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("renders test, testsuite, and testcase sections", () => {
    const dropdown = renderDropdown();
    const labels = dropdown.find("label");
    expect(labels.at(0).text()).toBe("Test (Optional)");
    expect(labels.at(1).text()).toBe("Testsuite (Optional)");
    expect(labels.at(2).text()).toBe("Testcase");
  });

  it("does not close when the trigger is clicked", () => {
    const trigger = document.createElement("button");
    document.body.appendChild(trigger);
    props.triggerRef = { current: trigger };
    render(<ExtendedSearchDropdown {...props} />);

    fireEvent.mouseDown(trigger);

    expect(props.onClose).not.toHaveBeenCalled();
    trigger.remove();
  });

  it("closes when clicking outside the dropdown and trigger", () => {
    const trigger = document.createElement("button");
    document.body.appendChild(trigger);
    props.triggerRef = { current: trigger };
    render(<ExtendedSearchDropdown {...props} />);

    fireEvent.mouseDown(document.body);

    expect(props.onClose).toHaveBeenCalledTimes(1);
    trigger.remove();
  });

  it("persists clearing the selected testcase", () => {
    props.value.selectedTestcase = "case1";
    props.value.selectedParams = { quantity: 1000 };
    props.value.searchText = "case1";
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("change", { target: { value: "" } });

    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "",
      selectedParams: {},
      searchText: "",
    });
  });

  it("keeps the selected testcase and opens all options on focus", () => {
    props.value.selectedTestcase = "case1";
    props.value.selectedParams = { quantity: 1000 };
    props.value.searchText = "case1";
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("focus");

    expect(dropdown.find("input").prop("value")).toBe("case1");
    expect(dropdown.find('button[role="option"]')).toHaveLength(1);
    expect(props.onStateChange).not.toHaveBeenCalled();
  });

  it("selects a testcase from the dropdown", () => {
    props.value.selectedTestcase = "case1";
    props.value.selectedParams = { quantity: 1000 };
    props.value.searchText = "case1";
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("click");
    dropdown.find('button[role="option"]').simulate("click");

    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "case1",
      selectedParams: {},
      searchText: "case1",
    });
  });

  it("allows editing a selected testcase as a normal combobox", () => {
    props.value.selectedTestcase = "case1";
    props.value.searchText = "case1";
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("change", {
      target: { value: "case" },
    });

    expect(dropdown.find("input").prop("value")).toBe("case");
    expect(dropdown.find('button[role="option"]')).toHaveLength(1);
    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "",
      selectedParams: {},
      searchText: "case",
    });
  });

  it("keeps the testcase name when typing an exact match", () => {
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("change", {
      target: { value: "case1" },
    });

    expect(dropdown.find("input").prop("value")).toBe("case1");
    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "case1",
      selectedParams: {},
      searchText: "case1",
    });
  });

  it("does not infer parameters when structured data is absent", () => {
    props.report = parametrizedReport(4, [
      {
        category: "testcase",
        name: "test_order <quantity=1000>",
        uid: "test_order__quantity_1000",
      },
      {
        category: "testcase",
        name: "test_order <quantity=5000>",
        uid: "test_order__quantity_5000",
      },
    ]);
    props.value.selectedTestcase = "test_order";
    props.value.searchText = "test_order";

    const dropdown = renderDropdown();

    expect(dropdown.text()).not.toContain("Filter by Parameters");
    expect(dropdown.find('[title^="Navigate to"]')).toHaveLength(2);
  });

  it("uses structured parameters when they are available", () => {
    props.report = parametrizedReport(4, [
      {
        category: "testcase",
        name: "test_order 0",
        uid: "test_order__0",
        parametrization_kwargs: {
          quantity: 1000,
          side: "Buy",
        },
      },
      {
        category: "testcase",
        name: "test_order 1",
        uid: "test_order__1",
        parametrization_kwargs: {
          quantity: 5000,
          side: "Sell",
        },
      },
    ]);
    props.value.selectedTestcase = "test_order";
    props.value.searchText = "test_order";

    const dropdown = renderDropdown();
    const labels = dropdown.find("label");

    expect(labels.map((label) => label.text())).toEqual([
      "Test (Optional)",
      "Testsuite (Optional)",
      "Testcase",
      "Filter by Parameters",
      "quantity",
      "side",
      "Permutations (2)",
    ]);
    expect(dropdown.find('[title^="Navigate to"]')).toHaveLength(2);
  });

  it("navigates using the propagated UID chain", () => {
    props.report = parametrizedReport(4, [
      {
        category: "testcase",
        name: "test_order 0",
        uid: "test_order__0",
        parametrization_kwargs: { quantity: 1000 },
      },
    ]);
    props.report.entries[0].name = "MyTest - part(7/10)";
    props.report.entries[0].definition_name = "MyTest";
    props.report.entries[0].part = [7, 10];
    props.value.selectedTestcase = "test_order";
    props.value.searchText = "test_order";

    const dropdown = renderDropdown();
    dropdown.find('[title^="Navigate to"]').simulate("click");

    expect(props.onNavigate).toHaveBeenCalledWith([
      "report-v4",
      "mt1",
      "ts1",
      "test_order",
      "test_order__0",
    ]);
    expect(props.handleNavFilter).toHaveBeenCalledWith({
      text:
        're:"^MyTest - part\\(7/10\\)$" ' +
        're:"^MySuite$" re:"^test_order 0$"',
      filters: [
        {
          type: "regexp",
          search: "^MyTest - part\\(7/10\\)$",
        },
        { type: "regexp", search: "^MySuite$" },
        { type: "regexp", search: "^test_order 0$" },
      ],
    });
  });

  it("keeps filters valid for testcase names containing quotes", () => {
    props.report = parametrizedReport(4, [
      {
        category: "testcase",
        name: 'test_order "quoted"',
        uid: "test_order__quoted",
        parametrization_kwargs: { quantity: 1000 },
      },
    ]);
    props.value.selectedTestcase = "test_order";
    props.value.searchText = "test_order";

    renderDropdown().find('[title^="Navigate to"]').simulate("click");

    expect(props.handleNavFilter).toHaveBeenCalledWith({
      text: "",
      filters: [
        { type: "regexp", search: "^MyTest$" },
        { type: "regexp", search: "^MySuite$" },
        {
          type: "regexp",
          search: '^test_order "quoted"$',
        },
      ],
    });
  });

  it("uses full UID keys and exactly filters multitests sharing a prefix", () => {
    props.report = parametrizedReport(4, [
      {
        category: "testcase",
        name: "test_order 0",
        uid: "test_order__0",
        parametrization_kwargs: { quantity: 1000 },
      },
    ]);
    const secondMultitest = JSON.parse(JSON.stringify(props.report.entries[0]));
    secondMultitest.name = "MyTest2";
    secondMultitest.uid = "mt2";
    secondMultitest.entries[0].entries[0].entries[0].uids[1] = "mt2";
    props.report.entries.push(secondMultitest);
    const addLogs = (entry) => {
      entry.logs = [];
      if (entry.category === "testcase") {
        entry.type = "TestCaseReport";
      }
      (entry.entries || []).forEach(addLogs);
    };
    addLogs(props.report);
    props.report = PropagateIndices(props.report);
    props.value.selectedTestcase = "test_order";
    props.value.searchText = "test_order";

    const resultItems = renderDropdown().find('[title^="Navigate to"]');

    expect(resultItems.map((item) => item.key())).toEqual([
      "report-v4/mt1/ts1/test_order/test_order__0",
      "report-v4/mt2/ts1/test_order/test_order__0",
    ]);

    resultItems.at(0).simulate("click");
    const { filters } = props.handleNavFilter.mock.calls[0][0];
    const filtered = filterEntries(props.report.entries, filters);

    expect(filtered.map((entry) => entry.name)).toEqual(["MyTest"]);
  });
});

describe("ExtendedSearchDropdown helpers", () => {
  describe("collectTestcases", () => {
    it.each([null, []])("returns an empty array for %p", (entries) => {
      expect(collectTestcases(entries)).toEqual([]);
    });

    it("collects testcases from nested report structure", () => {
      const entries = [
        {
          category: "multitest",
          name: "MyTest",
          uid: "mt1",
          entries: [
            {
              category: "testsuite",
              name: "MySuite",
              uid: "ts1",
              entries: [
                {
                  category: "testcase",
                  name: "case1",
                  uid: "tc1",
                },
              ],
            },
          ],
        },
      ];

      const result = collectTestcases(entries);
      expect(result).toHaveLength(1);
      expect(result[0].entry.name).toBe("case1");
      expect(result[0].testName).toBe("MyTest");
      expect(result[0].testsuiteName).toBe("MySuite");
      expect(result[0].baseName).toBe("case1");
    });

    it("groups testcases from all parts under the multitest definition", () => {
      const makePart = (index) => ({
        category: "multitest",
        name: `MyTest - part(${index}/2)`,
        definition_name: "MyTest",
        part: [index, 2],
        uid: `mt${index}`,
        entries: [
          {
            category: "testsuite",
            name: "MySuite",
            uid: `ts${index}`,
            entries: [
              {
                category: "parametrization",
                name: "case1",
                uid: `params${index}`,
                entries: [
                  {
                    category: "testcase",
                    name: `case1__${index}`,
                    uid: `tc${index}`,
                  },
                ],
              },
            ],
          },
        ],
      });

      const result = collectTestcases([makePart(0), makePart(1)]);

      expect(result.map((testcase) => testcase.testName)).toEqual([
        "MyTest",
        "MyTest",
      ]);
      expect(result.map((testcase) => testcase.testsuiteName)).toEqual([
        "MySuite",
        "MySuite",
      ]);
    });

    it("does not recurse into testcase assertion entries", () => {
      const entries = [
        {
          category: "testcase",
          type: "TestCaseReport",
          name: "case1",
          uid: "tc1",
          entries: [
            {
              category: "testcase",
              name: "assertion-like entry",
              uid: "nested",
            },
          ],
        },
      ];

      const result = collectTestcases(entries);

      expect(result).toHaveLength(1);
      expect(result[0].entry.uid).toBe("tc1");
    });

    it("groups permutations using their parent report", () => {
      const entries = [
        {
          category: "parametrization",
          name: "test_order",
          uid: "test_order",
          entries: [
            {
              category: "testcase",
              name: "test_order 0",
              uid: "test_order__0",
            },
            {
              category: "testcase",
              name: "test_order 1",
              uid: "test_order__1",
            },
          ],
        },
      ];

      const result = collectTestcases(entries);

      expect(result).toHaveLength(2);
      expect(result[0].baseName).toBe("test_order");
      expect(result[1].baseName).toBe("test_order");
      expect(result[0].parametrizationUid).toBe("test_order");
    });

    it("handles a report subtree with more than 100000 testcases", () => {
      const entries = [
        {
          category: "multitest",
          name: "large",
          entries: Array.from({ length: 125000 }, (_, index) => ({
            category: "testcase",
            name: `case${index}`,
            uid: `case${index}`,
          })),
        },
      ];

      expect(collectTestcases(entries)).toHaveLength(125000);
    });
  });

  describe("parameter value tokens", () => {
    it("uses type-aware tokens", () => {
      expect(paramValueToken(1)).not.toBe(paramValueToken("1"));
      expect(paramValueToken(false)).not.toBe(paramValueToken("false"));
    });
  });

  describe("buildFilterOptions", () => {
    it("builds unique sorted values per param key", () => {
      const perms = [
        { params: { side: "BUY", market: "PS" } },
        { params: { side: "SELL", market: "PS" } },
        { params: { side: "BUY", market: "HK" } },
      ];
      const result = buildFilterOptions(perms);
      expect(result.side).toEqual(["BUY", "SELL"]);
      expect(result.market).toEqual(["HK", "PS"]);
    });

    it("preserves types and sorts numeric values numerically", () => {
      const perms = [
        { params: { quantity: 10, value: 1 } },
        { params: { quantity: 9, value: "1" } },
        { params: { quantity: 100, value: 1 } },
      ];

      const result = buildFilterOptions(perms);

      expect(result.quantity).toEqual([9, 10, 100]);
      expect(result.value).toEqual([1, "1"]);
    });

    it("sorts mixed parameter values consistently", () => {
      const perms = [
        { params: { value: 1000 } },
        { params: { value: "1000" } },
        { params: { value: true } },
        { params: { value: null } },
        { params: { value: "" } },
        { params: { value: 2.5 } },
        { params: { value: 500 } },
      ];

      expect(buildFilterOptions(perms).value).toEqual([
        "",
        2.5,
        500,
        1000,
        "1000",
        null,
        true,
      ]);
    });
  });

  describe("applyParamFilters", () => {
    const perms = [
      { params: { side: "BUY", qty: "100" } },
      { params: { side: "SELL", qty: "100" } },
      { params: { side: "BUY", qty: "200" } },
    ];

    it("returns all when no filters selected", () => {
      expect(applyParamFilters(perms, {})).toHaveLength(3);
    });

    it("filters by multiple params", () => {
      const result = applyParamFilters(perms, { side: "BUY", qty: "100" });
      expect(result).toHaveLength(1);
    });

    it("treats empty string and null as real parameter values", () => {
      const nullable = [
        { params: { note: null } },
        { params: { note: "" } },
        { params: { note: "hello" } },
      ];

      expect(applyParamFilters(nullable, { note: null })).toEqual([
        nullable[0],
      ]);
      expect(applyParamFilters(nullable, { note: "" })).toEqual([nullable[1]]);
    });

    it("distinguishes structured values by type", () => {
      const typed = [
        { params: { value: 1, enabled: false } },
        { params: { value: "1", enabled: "false" } },
      ];

      expect(applyParamFilters(typed, { value: 1 })).toEqual([typed[0]]);
      expect(applyParamFilters(typed, { enabled: false })).toEqual([typed[0]]);
    });
  });
});
