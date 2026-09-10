import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { fireEvent, render } from "@testing-library/react";

import ExtendedSearchDropdown, {
  collectTestcases,
  getPermutations,
  enrichWithParams,
  paramValueToken,
  formatParamValue,
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
    persistedState: {
      selectedTest: "",
      selectedTestsuite: "",
      selectedTestcase: "",
      selectedParams: {},
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
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
  });

  it("shallow renders without crashing", () => {
    renderDropdown();
  });

  it("shallow renders the correct HTML structure", () => {
    const dropdown = renderDropdown();
    expect(dropdown).toMatchSnapshot();
  });

  it("renders test, testsuite, and testcase sections", () => {
    const dropdown = renderDropdown();
    const labels = dropdown.find('[data-testid="section-label"]');
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
    props.persistedState.selectedTestcase = "case1";
    props.persistedState.selectedParams = { quantity: 1000 };
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("change", { target: { value: "" } });

    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "",
      selectedParams: {},
    });
  });

  it("keeps the selected testcase and opens all options on focus", () => {
    props.persistedState.selectedTestcase = "case1";
    props.persistedState.selectedParams = { quantity: 1000 };
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("focus");

    expect(dropdown.find("input").prop("value")).toBe("case1");
    expect(dropdown.find('[data-testid="testcase-option"]')).toHaveLength(1);
    expect(props.onStateChange).not.toHaveBeenCalled();
  });

  it("selects a testcase from the dropdown", () => {
    props.persistedState.selectedTestcase = "case1";
    props.persistedState.selectedParams = { quantity: 1000 };
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("click");
    dropdown.find('[data-testid="testcase-option"]').simulate("click");

    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "case1",
      selectedParams: {},
    });
  });

  it("allows editing a selected testcase as a normal combobox", () => {
    props.persistedState.selectedTestcase = "case1";
    const dropdown = renderDropdown();

    dropdown.find("input").simulate("change", {
      target: { value: "case" },
    });

    expect(dropdown.find("input").prop("value")).toBe("case");
    expect(dropdown.find('[data-testid="testcase-option"]')).toHaveLength(1);
    expect(props.onStateChange).toHaveBeenLastCalledWith({
      selectedTestcase: "",
      selectedParams: {},
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
    props.persistedState.selectedTestcase = "test_order";

    const dropdown = renderDropdown();

    expect(dropdown.find('[data-testid="param-label"]')).toHaveLength(0);
    expect(dropdown.find('[data-testid="result-item"]')).toHaveLength(2);
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
    props.persistedState.selectedTestcase = "test_order";

    const dropdown = renderDropdown();
    const labels = dropdown.find('[data-testid="param-label"]');

    expect(labels.map((label) => label.text())).toEqual(["quantity", "side"]);
    expect(dropdown.find('[data-testid="result-item"]')).toHaveLength(2);
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
    props.persistedState.selectedTestcase = "test_order";

    const dropdown = renderDropdown();
    dropdown.find('[data-testid="result-item"]').simulate("click");

    expect(props.onNavigate).toHaveBeenCalledWith([
      "report-v4",
      "mt1",
      "ts1",
      "test_order",
      "test_order__0",
    ]);
    expect(props.handleNavFilter).toHaveBeenCalledWith({
      text: 'mt:"MyTest" s:"MySuite" re:"^test_order 0$"',
      filters: [
        { type: "test", search: ["MyTest"] },
        { type: "suite", search: ["MySuite"] },
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
    props.persistedState.selectedTestcase = "test_order";

    renderDropdown().find('[data-testid="result-item"]').simulate("click");

    expect(props.handleNavFilter).toHaveBeenCalledWith({
      text: "",
      filters: [
        { type: "test", search: ["MyTest"] },
        { type: "suite", search: ["MySuite"] },
        {
          type: "regexp",
          search: '^test_order "quoted"$',
        },
      ],
    });
  });

  it("uses the full UID chain for result keys", () => {
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
    props.persistedState.selectedTestcase = "test_order";

    const resultItems = renderDropdown().find('[data-testid="result-item"]');

    expect(resultItems.map((item) => item.key())).toEqual([
      "report-v4/mt1/ts1/test_order/test_order__0",
      "report-v4/mt2/ts1/test_order/test_order__0",
    ]);
  });
});

describe("ExtendedSearchDropdown helpers", () => {
  describe("collectTestcases", () => {
    it("returns empty array for null entries", () => {
      expect(collectTestcases(null)).toEqual([]);
    });

    it("returns empty array for empty entries", () => {
      expect(collectTestcases([])).toEqual([]);
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

    it("preserves testName/testsuiteName hierarchy", () => {
      const entries = [
        {
          category: "multitest",
          name: "Test1",
          uid: "mt1",
          entries: [
            {
              category: "testsuite",
              name: "Suite1",
              uid: "ts1",
              entries: [
                {
                  category: "testcase",
                  name: "caseA",
                  uid: "tc1",
                },
                {
                  category: "testcase",
                  name: "caseB",
                  uid: "tc2",
                },
              ],
            },
          ],
        },
      ];

      const result = collectTestcases(entries);
      expect(result).toHaveLength(2);
      expect(result[0].testName).toBe("Test1");
      expect(result[0].testsuiteName).toBe("Suite1");
      expect(result[1].testName).toBe("Test1");
      expect(result[1].testsuiteName).toBe("Suite1");
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
      expect(
        getPermutations(result, "MyTest", "MySuite", "case1")
      ).toHaveLength(2);
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

  describe("getPermutations", () => {
    const testcases = [
      { testName: "T1", testsuiteName: "S1", baseName: "caseA" },
      { testName: "T1", testsuiteName: "S1", baseName: "caseB" },
      { testName: "T1", testsuiteName: "S2", baseName: "caseA" },
      { testName: "T2", testsuiteName: "S3", baseName: "caseA" },
    ];

    it("filters by baseName only when test/suite empty", () => {
      const result = getPermutations(testcases, "", "", "caseA");
      expect(result).toHaveLength(3);
    });

    it("filters by test and baseName", () => {
      const result = getPermutations(testcases, "T1", "", "caseA");
      expect(result).toHaveLength(2);
    });

    it("filters by test, suite, and baseName", () => {
      const result = getPermutations(testcases, "T1", "S1", "caseA");
      expect(result).toHaveLength(1);
    });

    it("returns empty when no match", () => {
      const result = getPermutations(testcases, "T1", "S1", "noMatch");
      expect(result).toEqual([]);
    });
  });

  describe("enrichWithParams", () => {
    it("uses structured parameters and preserves their types", () => {
      const perms = [
        {
          entry: {
            name: "test 0",
            parametrization_kwargs: {
              quantity: 1000,
              side: "Buy",
              enabled: true,
            },
          },
        },
      ];

      expect(enrichWithParams(perms)[0].params).toEqual({
        quantity: 1000,
        side: "Buy",
        enabled: true,
      });
    });
  });

  describe("parameter value formatting", () => {
    it("uses type-aware tokens", () => {
      expect(paramValueToken(1)).not.toBe(paramValueToken("1"));
      expect(paramValueToken(false)).not.toBe(paramValueToken("false"));
    });

    it("formats structured values for display", () => {
      expect(formatParamValue(1000)).toBe("1000");
      expect(formatParamValue(true)).toBe("true");
      expect(formatParamValue("Buy")).toBe("Buy");
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

    it("returns empty object for no permutations", () => {
      expect(buildFilterOptions([])).toEqual({});
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

    it("filters by single param", () => {
      const result = applyParamFilters(perms, { side: "BUY" });
      expect(result).toHaveLength(2);
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

    it("handles falsy values like '0' correctly", () => {
      const withZero = [{ params: { qty: "0" } }, { params: { qty: "100" } }];
      const result = applyParamFilters(withZero, { qty: "0" });
      expect(result).toHaveLength(1);
      expect(result[0].params.qty).toBe("0");
    });

    it("handles 'false' as a valid filter value", () => {
      const withFalse = [
        { params: { enabled: "false" } },
        { params: { enabled: "true" } },
      ];
      const result = applyParamFilters(withFalse, { enabled: "false" });
      expect(result).toHaveLength(1);
      expect(result[0].params.enabled).toBe("false");
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
