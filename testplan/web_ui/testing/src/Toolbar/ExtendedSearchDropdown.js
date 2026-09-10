import React, {
  useState,
  useMemo,
  useEffect,
  useRef,
} from "react";
import PropTypes from "prop-types";
import _ from "lodash";

import "./ExtendedSearchDropdown.css";
import { isReportLeaf } from "../Report/reportUtils";

/**
 * Recursively collect testcases with hierarchy
 * context from the report tree.
 */
const collectTestcases = (
  entries,
  testName = "",
  testsuiteName = "",
  parametrization = null
) =>
  _.reduce(
    entries || [],
    (result, entry) => {
      const curTest =
        entry.category === "multitest"
          ? Array.isArray(entry.part)
            ? entry.definition_name || entry.name
            : entry.name
          : testName;
      const curSuite =
        entry.category === "testsuite"
          ? entry.name
          : testsuiteName;
      const curParametrization =
        entry.category === "parametrization"
          ? entry
          : parametrization;

      if (entry.category === "testcase") {
        result.push({
          entry,
          baseName:
            curParametrization?.name ||
            entry.name,
          parametrizationUid:
            curParametrization?.uid || "",
          testName: curTest,
          testsuiteName: curSuite,
        });
      }
      if (
        !isReportLeaf(entry) &&
        !_.isEmpty(entry.entries)
      ) {
        result.push(
          ...collectTestcases(
            entry.entries,
            curTest,
            curSuite,
            curParametrization
          )
        );
      }
      return result;
    },
    []
  );

/**
 * Extract unique sorted values for a field,
 * optionally pre-filtered by other fields.
 */
const getUniqueField = (
  list,
  field,
  filters = {}
) => {
  const filtered = _.reduce(
    Object.entries(filters),
    (items, [k, v]) =>
      v
        ? _.filter(items, (item) => item[k] === v)
        : items,
    list
  );
  return _(filtered)
    .map(field)
    .compact()
    .uniq()
    .sortBy()
    .value();
};

/**
 * Get permutations matching test, testsuite and
 * base testcase name.
 */
const getPermutations = (
  testcases,
  testName,
  testsuiteName,
  baseName
) =>
  _.filter(
    testcases,
    (tc) =>
      (!testName ||
        tc.testName === testName) &&
      (!testsuiteName ||
        tc.testsuiteName === testsuiteName) &&
      tc.baseName === baseName
  );

const enrichWithParams = (perms) =>
  _.map(perms, (p) => ({
    ...p,
    params: p.entry.parametrization_kwargs || {},
  }));

const paramValueToken = (value) =>
  `${typeof value}:${JSON.stringify(value)}`;

const formatParamValue = (value) =>
  typeof value === "string"
    ? value
    : JSON.stringify(value);

const compareParamValues = (left, right) => {
  if (
    typeof left === "number" &&
    typeof right === "number"
  ) {
    return left - right;
  }
  return formatParamValue(left).localeCompare(
    formatParamValue(right)
  );
};

/**
 * Build { paramKey: [uniqueValues] } from
 * permutations for dynamic filter dropdowns.
 */
const buildFilterOptions = (perms) =>
  _(perms)
    .flatMap((p) => _.toPairs(p.params))
    .groupBy(0)
    .mapValues((pairs) =>
      _(pairs)
        .map(1)
        .uniqBy(paramValueToken)
        .sort(compareParamValues)
        .value()
    )
    .value();

/**
 * Filter permutations by selected param values.
 * Empty/null values are treated as "Any".
 */
const applyParamFilters = (perms, selected) =>
  _.filter(perms, (p) =>
    _.every(
      Object.entries(selected),
      ([k, v]) =>
        v === "" ||
        v == null ||
        _.isEqual(p.params[k], v)
    )
  );

/**
 * Extended Search Dropdown Component.
 * Allows searching testcases by report hierarchy
 * (Test -> Testsuite -> Testcase) and by
 * structured parameters.
 */
const ExtendedSearchDropdown = ({
  report,
  onNavigate,
  onClose,
  handleNavFilter,
  persistedState,
  onStateChange,
  triggerRef,
}) => {
  const testcaseOptionsId = "ext-search-tc-list";

  // State initialised from persisted values
  const [selectedTest, setSelectedTest] = useState(
    persistedState?.selectedTest || ""
  );
  const [
    selectedTestsuite,
    setSelectedTestsuite,
  ] = useState(
    persistedState?.selectedTestsuite || ""
  );
  const [
    selectedTestcase,
    setSelectedTestcase,
  ] = useState(
    persistedState?.selectedTestcase || ""
  );
  const [searchText, setSearchText] = useState("");
  const [showTestcaseOptions, setShowTestcaseOptions] =
    useState(false);
  const [selectedParams, setSelectedParams] =
    useState(persistedState?.selectedParams || {});

  const dropdownRef = useRef(null);
  const reportUid = report?.uid;

  // --- Derived data (memoised) ---

  const allTestcases = useMemo(() => {
    if (!report || !report.entries) return [];
    return collectTestcases(report.entries);
  }, [report]);

  const uniqueTestNames = useMemo(
    () =>
      getUniqueField(allTestcases, "testName"),
    [allTestcases]
  );

  const uniqueTestsuiteNames = useMemo(
    () =>
      getUniqueField(
        allTestcases,
        "testsuiteName",
        { testName: selectedTest }
      ),
    [allTestcases, selectedTest]
  );

  const uniqueTestcaseNames = useMemo(
    () =>
      getUniqueField(allTestcases, "baseName", {
        testName: selectedTest,
        testsuiteName: selectedTestsuite,
      }),
    [allTestcases, selectedTest, selectedTestsuite]
  );

  const filteredTestcaseNames = useMemo(() => {
    if (!searchText.trim()) {
      return uniqueTestcaseNames;
    }
    const lower = searchText.toLowerCase();
    return _.filter(
      uniqueTestcaseNames,
      (name) =>
        name.toLowerCase().includes(lower)
    );
  }, [uniqueTestcaseNames, searchText]);

  const permutations = useMemo(() => {
    if (!selectedTestcase) return [];
    const raw = getPermutations(
      allTestcases,
      selectedTest,
      selectedTestsuite,
      selectedTestcase
    );
    return enrichWithParams(raw);
  }, [
    allTestcases,
    selectedTest,
    selectedTestsuite,
    selectedTestcase,
  ]);

  const filterOptions = useMemo(
    () => buildFilterOptions(permutations),
    [permutations]
  );

  const filteredPermutations = useMemo(
    () =>
      applyParamFilters(
        permutations,
        selectedParams
      ),
    [permutations, selectedParams]
  );

  // --- Click outside / Escape to close ---

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target) &&
        !triggerRef?.current?.contains(e.target)
      ) {
        onClose();
      }
    };
    const handleEscape = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener(
      "mousedown",
      handleClickOutside
    );
    document.addEventListener(
      "keydown",
      handleEscape
    );
    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
      document.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, [onClose, triggerRef]);

  // --- Handlers ---

  const persistState = (patch) => {
    if (onStateChange) {
      onStateChange(patch);
    }
  };

  const handleTestChange = (e) => {
    const value = e.target.value;
    setSelectedTest(value);
    setSelectedTestsuite("");
    setSelectedTestcase("");
    setSelectedParams({});
    setSearchText("");
    setShowTestcaseOptions(false);
    persistState({
      selectedTest: value,
      selectedTestsuite: "",
      selectedTestcase: "",
      selectedParams: {},
    });
  };

  const handleTestsuiteChange = (e) => {
    const value = e.target.value;
    setSelectedTestsuite(value);
    setSelectedTestcase("");
    setSelectedParams({});
    setSearchText("");
    setShowTestcaseOptions(false);
    persistState({
      selectedTestsuite: value,
      selectedTestcase: "",
      selectedParams: {},
    });
  };

  const handleTestcaseSearch = (e) => {
    const value = e.target.value;
    if (_.includes(uniqueTestcaseNames, value)) {
      setSelectedTestcase(value);
      setSearchText("");
      setShowTestcaseOptions(false);
      setSelectedParams({});
      persistState({
        selectedTestcase: value,
        selectedParams: {},
      });
    } else {
      setSelectedTestcase("");
      setSearchText(value);
      setShowTestcaseOptions(true);
      setSelectedParams({});
      persistState({
        selectedTestcase: "",
        selectedParams: {},
      });
    }
  };

  const handleTestcaseFocus = () => {
    setShowTestcaseOptions(true);
  };

  const handleTestcaseSelect = (value) => {
    setSelectedTestcase(value);
    setSearchText("");
    setShowTestcaseOptions(false);
    setSelectedParams({});
    persistState({
      selectedTestcase: value,
      selectedParams: {},
    });
  };

  const handleParamChange = (key, token) => {
    const newParams = { ...selectedParams };
    if (token === "") {
      delete newParams[key];
    } else {
      newParams[key] = _.find(
        filterOptions[key],
        (value) => paramValueToken(value) === token
      );
    }
    setSelectedParams(newParams);
    persistState({ selectedParams: newParams });
  };

  /**
   * Navigate to a specific permutation.
   * Replaces any existing filter text with a
   * targeted suite+case filter for the selected
   * permutation, then navigates via UID path.
   */
  const handleResultClick = (permutation) => {
    if (!onNavigate || !reportUid) return;

    if (handleNavFilter) {
      const name = permutation.entry.name;
      const escaped = name.replace(/"/g, '\\"');
      const suite = permutation.testsuiteName;
      const filters = [];
      let text = "";
      // Filter by testsuite if available
      if (suite) {
        const escapedSuite =
          suite.replace(/"/g, '\\"');
        filters.push({
          type: "suite",
          search: [suite],
        });
        text += `s:"${escapedSuite}" `;
      }
      // Filter by testcase name
      filters.push({
        type: "case",
        search: [name],
      });
      text += `c:"${escaped}"`;
      handleNavFilter({ text, filters });
    }

    onNavigate(permutation.entry.uids);
    onClose();
  };

  const handleResultKeyDown = (e, perm) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleResultClick(perm);
    }
  };

  // --- Render ---

  const paramKeys = _.keys(filterOptions);
  const hasTestcases =
    uniqueTestcaseNames.length > 0;
  const isParametrized = _.some(
    permutations,
    (permutation) => permutation.parametrizationUid
  );

  return (
    <div
      ref={dropdownRef}
      className="extended-search-dropdown"
      role="dialog"
      aria-label="Extended Search"
    >
      {/* Test/Multitest (Optional) */}
      <div className="extended-search-section">
        <label className="extended-search-label">
          Test (Optional)
        </label>
        <select
          className="extended-search-select"
          value={selectedTest}
          onChange={handleTestChange}
        >
          <option value="">
            -- All Tests --
          </option>
          {uniqueTestNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Testsuite (Optional) */}
      <div className="extended-search-section">
        <label className="extended-search-label">
          Testsuite (Optional)
        </label>
        <select
          className="extended-search-select"
          value={selectedTestsuite}
          onChange={handleTestsuiteChange}
        >
          <option value="">
            -- All Testsuites --
          </option>
          {uniqueTestsuiteNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Testcase (Mandatory) */}
      <div className="extended-search-section">
        <label className="extended-search-label">
          Testcase
        </label>
        <div className="extended-search-testcase-picker">
          <input
            type="text"
            className="extended-search-select"
            placeholder="Type to search or select..."
            value={selectedTestcase || searchText}
            onChange={handleTestcaseSearch}
            onFocus={handleTestcaseFocus}
            onClick={handleTestcaseFocus}
            autoComplete="off"
            role="combobox"
            aria-expanded={showTestcaseOptions}
            aria-controls={testcaseOptionsId}
          />
          {showTestcaseOptions && (
            <div
              id={testcaseOptionsId}
              className="extended-search-testcase-options"
              role="listbox"
            >
              {filteredTestcaseNames.length === 0 ? (
                <div className="extended-search-no-results">
                  No matching testcases found
                </div>
              ) : (
                filteredTestcaseNames.map((name) => (
                  <button
                    key={name}
                    type="button"
                    className="extended-search-testcase-option"
                    role="option"
                    aria-selected={name === selectedTestcase}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => handleTestcaseSelect(name)}
                  >
                    {name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Parameter Filters */}
      {selectedTestcase &&
        paramKeys.length > 0 && (
          <div className="extended-search-section">
            <label className="extended-search-label">
              Filter by Parameters
            </label>
            <div className="extended-search-params-grid">
              {paramKeys.map((key) => (
                <div
                  key={key}
                  className="extended-search-param-item"
                >
                  <label className="extended-search-param-label">
                    {key.replace(/_/g, " ")}
                  </label>
                  <select
                    className="extended-search-select"
                    style={{ marginBottom: "0" }}
                    value={
                      key in selectedParams
                        ? paramValueToken(
                            selectedParams[key]
                          )
                        : ""
                    }
                    onChange={(e) =>
                      handleParamChange(
                        key,
                        e.target.value
                      )
                    }
                  >
                    <option value="">Any</option>
                    {filterOptions[key].map(
                      (val) => (
                        <option
                          key={paramValueToken(val)}
                          value={paramValueToken(val)}
                        >
                          {formatParamValue(val)}
                        </option>
                      )
                    )}
                  </select>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* No params message */}
      {selectedTestcase &&
        paramKeys.length === 0 && (
          <div className="extended-search-section">
            <div className="extended-search-no-results">
              {isParametrized
                ? "Parameter data is unavailable in this report. "
                : "No parameters found. "}
              Showing all matching testcases.
            </div>
          </div>
        )}

      {/* Results */}
      {selectedTestcase && (
        <div
          className={[
            "extended-search-section",
            "extended-search-section-last",
          ].join(" ")}
        >
          <label className="extended-search-label">
            Permutations (
            {filteredPermutations.length})
          </label>
          <div
            className="extended-search-results"
            role="listbox"
            aria-label="Matching permutations"
          >
            {filteredPermutations.length === 0 ? (
              <div className="extended-search-no-results">
                No matching permutations found
              </div>
            ) : (
              filteredPermutations.map(
                (perm, index) => (
                  <div
                    key={perm.entry.uids.join("/")}
                    className={[
                      "extended-search-result-item",
                      index ===
                        filteredPermutations.length -
                          1 &&
                        "extended-search-result-item-last",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    role="option"
                    aria-selected={false}
                    tabIndex={0}
                    onClick={() =>
                      handleResultClick(perm)
                    }
                    onKeyDown={(e) =>
                      handleResultKeyDown(e, perm)
                    }
                    title={`Navigate to ${perm.entry.name}`}
                  >
                    {perm.entry.name}
                  </div>
                )
              )
            )}
          </div>
        </div>
      )}

      {/* Prompt when no testcase selected */}
      {!selectedTestcase && hasTestcases && (
        <div className="extended-search-no-results">
          Select a testcase to see permutations
        </div>
      )}

      {/* Loading or empty */}
      {!report && (
        <div className="extended-search-no-results">
          Loading report data...
        </div>
      )}
      {report && !hasTestcases && (
        <div className="extended-search-no-results">
          No testcases found in report
        </div>
      )}
    </div>
  );
};

ExtendedSearchDropdown.propTypes = {
  /** The testplan report object */
  report: PropTypes.object,
  /** Callback when navigating to a permutation */
  onNavigate: PropTypes.func.isRequired,
  /** Callback to close the dropdown */
  onClose: PropTypes.func.isRequired,
  /** Callback to filter report (like search) */
  handleNavFilter: PropTypes.func,
  /** Persisted state from parent */
  persistedState: PropTypes.shape({
    selectedTest: PropTypes.string,
    selectedTestsuite: PropTypes.string,
    selectedTestcase: PropTypes.string,
    selectedParams: PropTypes.object,
  }),
  /** Callback to persist state to parent */
  onStateChange: PropTypes.func,
  /** Ref to the button that toggles the dropdown */
  triggerRef: PropTypes.shape({ current: PropTypes.any }),
};

export default ExtendedSearchDropdown;

export {
  collectTestcases,
  getPermutations,
  enrichWithParams,
  paramValueToken,
  formatParamValue,
  buildFilterOptions,
  applyParamFilters,
};
