import React, { useState, useMemo, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import _ from "lodash";
import { StyleSheet, css } from "aphrodite";

import { isReportLeaf } from "../Report/reportUtils";

/**
 * Recursively collect testcases with hierarchy
 * context from the report tree.
 */
const collectTestcases = (
  entries,
  testName = "",
  testsuiteName = "",
  parametrization = null,
  result = [],
  reportTestName = ""
) => {
  _.forEach(entries || [], (entry) => {
    const curTest =
      entry.category === "multitest"
        ? Array.isArray(entry.part)
          ? entry.definition_name || entry.name
          : entry.name
        : testName;
    const curReportTest =
      entry.category === "multitest" ? entry.name : reportTestName;
    const curSuite =
      entry.category === "testsuite" ? entry.name : testsuiteName;
    const curParametrization =
      entry.category === "parametrization" ? entry : parametrization;

    if (entry.category === "testcase") {
      result.push({
        entry,
        baseName: curParametrization?.name || entry.name,
        parametrizationUid: curParametrization?.uid || "",
        testName: curTest,
        reportTestName: curReportTest,
        testsuiteName: curSuite,
      });
    }
    if (!isReportLeaf(entry) && !_.isEmpty(entry.entries)) {
      collectTestcases(
        entry.entries,
        curTest,
        curSuite,
        curParametrization,
        result,
        curReportTest
      );
    }
  });
  return result;
};

/**
 * Extract unique sorted values for a field,
 * optionally pre-filtered by other fields.
 */
const getUniqueField = (list, field, filters = {}) => {
  const filtered = _.reduce(
    Object.entries(filters),
    (items, [k, v]) => (v ? _.filter(items, (item) => item[k] === v) : items),
    list
  );
  return _(filtered).map(field).compact().uniq().sortBy().value();
};

const paramValueToken = (value) => `${typeof value}:${JSON.stringify(value)}`;

const formatParamValue = (value) =>
  typeof value === "string" ? value : JSON.stringify(value);

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
        .sort((left, right) =>
          String(left).localeCompare(String(right), undefined, {
            numeric: true,
          })
        )
        .value()
    )
    .value();

/**
 * Filter permutations by selected param values.
 * A key is present only when that filter is active, so null and empty string
 * remain valid parameter values.
 */
const applyParamFilters = (perms, selected) =>
  _.filter(perms, (p) =>
    _.every(Object.entries(selected), ([k, v]) => _.isEqual(p.params[k], v))
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
  value,
  onStateChange,
  triggerRef,
}) => {
  const testcaseOptionsId = "ext-search-tc-list";
  const {
    selectedTest,
    selectedTestsuite,
    selectedTestcase,
    selectedParams,
    searchText,
  } = value;
  const [showTestcaseOptions, setShowTestcaseOptions] = useState(false);

  const dropdownRef = useRef(null);
  const reportUid = report?.uid;
  const reportIdentity = report?.hash || report;

  const allTestcases = useMemo(() => {
    if (!report || !report.entries) return [];
    return collectTestcases(report.entries);
    // Interactive polling creates new report objects even when hash is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportIdentity]);

  const uniqueTestNames = useMemo(
    () => getUniqueField(allTestcases, "testName"),
    [allTestcases]
  );

  const uniqueTestsuiteNames = useMemo(
    () =>
      getUniqueField(allTestcases, "testsuiteName", { testName: selectedTest }),
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

  const filteredTestcaseNames = searchText.trim()
    ? _.filter(uniqueTestcaseNames, (name) =>
        name.toLowerCase().includes(searchText.toLowerCase())
      )
    : uniqueTestcaseNames;

  const permutations = useMemo(() => {
    if (!selectedTestcase) return [];
    return _(allTestcases)
      .filter(
        (testcase) =>
          (!selectedTest || testcase.testName === selectedTest) &&
          (!selectedTestsuite ||
            testcase.testsuiteName === selectedTestsuite) &&
          testcase.baseName === selectedTestcase
      )
      .map((testcase) => ({
        ...testcase,
        params: testcase.entry.parametrization_kwargs || {},
      }))
      .value();
  }, [allTestcases, selectedTest, selectedTestsuite, selectedTestcase]);

  const filterOptions = useMemo(
    () => buildFilterOptions(permutations),
    [permutations]
  );

  const filteredPermutations = useMemo(
    () => applyParamFilters(permutations, selectedParams),
    [permutations, selectedParams]
  );

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
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose, triggerRef]);

  const handleTestChange = (e) => {
    const value = e.target.value;
    setShowTestcaseOptions(false);
    onStateChange({
      selectedTest: value,
      selectedTestsuite: "",
      selectedTestcase: "",
      selectedParams: {},
      searchText: "",
    });
  };

  const handleTestsuiteChange = (e) => {
    const value = e.target.value;
    setShowTestcaseOptions(false);
    onStateChange({
      selectedTestsuite: value,
      selectedTestcase: "",
      selectedParams: {},
      searchText: "",
    });
  };

  const handleTestcaseSearch = (e) => {
    const value = e.target.value;
    if (_.includes(uniqueTestcaseNames, value)) {
      setShowTestcaseOptions(false);
      onStateChange({
        selectedTestcase: value,
        selectedParams: {},
        searchText: value,
      });
    } else {
      setShowTestcaseOptions(true);
      onStateChange({
        selectedTestcase: "",
        selectedParams: {},
        searchText: value,
      });
    }
  };

  const handleTestcaseFocus = () => {
    setShowTestcaseOptions(true);
  };

  const handleTestcaseSelect = (value) => {
    setShowTestcaseOptions(false);
    onStateChange({
      selectedTestcase: value,
      selectedParams: {},
      searchText: value,
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
    onStateChange({ selectedParams: newParams });
  };

  /**
   * Navigate to a specific permutation.
   * Replaces any existing filter text with a
   * targeted suite+case filter for the selected
   * permutation, then navigates via UID path.
   */
  const handleResultClick = (permutation) => {
    if (!reportUid) return;

    if (handleNavFilter) {
      const name = permutation.entry.name;
      const test = permutation.reportTestName || permutation.testName;
      const suite = permutation.testsuiteName;
      const filters = [];
      const textTerms = [];
      if (test) {
        filters.push({
          type: "regexp",
          search: `^${_.escapeRegExp(test)}$`,
        });
        if (!test.includes('"')) {
          textTerms.push(`re:"^${_.escapeRegExp(test)}$"`);
        }
      }
      if (suite) {
        filters.push({
          type: "regexp",
          search: `^${_.escapeRegExp(suite)}$`,
        });
        if (!suite.includes('"')) {
          textTerms.push(`re:"^${_.escapeRegExp(suite)}$"`);
        }
      }
      filters.push({
        type: "regexp",
        search: `^${_.escapeRegExp(name)}$`,
      });
      if (!name.includes('"')) {
        textTerms.push(`re:"^${_.escapeRegExp(name)}$"`);
      }
      handleNavFilter({
        text: textTerms.length === filters.length ? textTerms.join(" ") : "",
        filters,
      });
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

  const paramKeys = _.keys(filterOptions);
  const hasTestcases = uniqueTestcaseNames.length > 0;
  const isParametrized = _.some(
    permutations,
    (permutation) => permutation.parametrizationUid
  );

  return (
    <div
      ref={dropdownRef}
      className={css(styles.dropdown)}
      role="dialog"
      aria-label="Extended Search"
    >
      {/* Test/Multitest (Optional) */}
      <div className={css(styles.section)}>
        <label className={css(styles.label)}>
          Test (Optional)
        </label>
        <select
          className={css(styles.select)}
          value={selectedTest}
          onChange={handleTestChange}
        >
          <option value="">-- All Tests --</option>
          {uniqueTestNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Testsuite (Optional) */}
      <div className={css(styles.section)}>
        <label className={css(styles.label)}>
          Testsuite (Optional)
        </label>
        <select
          className={css(styles.select)}
          value={selectedTestsuite}
          onChange={handleTestsuiteChange}
        >
          <option value="">-- All Testsuites --</option>
          {uniqueTestsuiteNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Testcase (Mandatory) */}
      <div className={css(styles.section)}>
        <label className={css(styles.label)}>
          Testcase
        </label>
        <div>
          <input
            type="text"
            className={css(styles.select)}
            placeholder="Type to search or select..."
            value={searchText}
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
              className={css(styles.testcaseOptions)}
              role="listbox"
            >
              {filteredTestcaseNames.length === 0 ? (
                <div className={css(styles.noResults)}>
                  No matching testcases found
                </div>
              ) : (
                filteredTestcaseNames.map((name) => (
                  <button
                    key={name}
                    type="button"
                    className={css(
                      styles.testcaseOption,
                      name === selectedTestcase && styles.selectedOption
                    )}
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
      {selectedTestcase && paramKeys.length > 0 && (
        <div className={css(styles.section)}>
          <label className={css(styles.label)}>
            Filter by Parameters
          </label>
          <div className={css(styles.paramsGrid)}>
            {paramKeys.map((key) => (
              <div key={key} className={css(styles.paramItem)}>
                <label className={css(styles.paramLabel)}>
                  {key.replace(/_/g, " ")}
                </label>
                <select
                  className={css(styles.select, styles.paramSelect)}
                  value={
                    key in selectedParams
                      ? paramValueToken(selectedParams[key])
                      : ""
                  }
                  onChange={(e) => handleParamChange(key, e.target.value)}
                >
                  <option value="">Any</option>
                  {filterOptions[key].map((val) => (
                    <option
                      key={paramValueToken(val)}
                      value={paramValueToken(val)}
                    >
                      {formatParamValue(val)}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No params message */}
      {selectedTestcase && paramKeys.length === 0 && (
        <div className={css(styles.section)}>
          <div className={css(styles.noResults)}>
            {isParametrized
              ? "Parameter data is unavailable in this report. "
              : "No parameters found. "}
            Showing all matching testcases.
          </div>
        </div>
      )}

      {/* Results */}
      {selectedTestcase && (
        <div className={css(styles.section, styles.lastSection)}>
          <label className={css(styles.label)}>
            Permutations ({filteredPermutations.length})
          </label>
          <div
            className={css(styles.results)}
            role="listbox"
            aria-label="Matching permutations"
          >
            {filteredPermutations.length === 0 ? (
              <div className={css(styles.noResults)}>
                No matching permutations found
              </div>
            ) : (
              filteredPermutations.map((perm, index) => (
                <div
                  key={perm.entry.uids.join("/")}
                  className={css(
                    styles.resultItem,
                    index === filteredPermutations.length - 1 &&
                      styles.lastResultItem
                  )}
                  role="option"
                  aria-selected={false}
                  tabIndex={0}
                  onClick={() => handleResultClick(perm)}
                  onKeyDown={(e) => handleResultKeyDown(e, perm)}
                  title={`Navigate to ${perm.entry.name}`}
                >
                  {perm.entry.name}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Prompt when no testcase selected */}
      {!selectedTestcase && hasTestcases && (
        <div className={css(styles.noResults)}>
          Select a testcase to see permutations
        </div>
      )}

      {/* Loading or empty */}
      {!report && (
        <div className={css(styles.noResults)}>Loading report data...</div>
      )}
      {report && !hasTestcases && (
        <div className={css(styles.noResults)}>
          No testcases found in report
        </div>
      )}
    </div>
  );
};

const styles = StyleSheet.create({
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    marginTop: "8px",
    width: "100%",
    minWidth: "min(400px, 100%)",
    maxWidth: "500px",
    maxHeight: "550px",
    overflowY: "auto",
    backgroundColor: "#ffffff",
    border: "1px solid #d0d0d0",
    borderRadius: "6px",
    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.15)",
    zIndex: 1000,
    padding: "16px",
  },
  select: {
    width: "100%",
    padding: "8px 12px",
    marginBottom: "8px",
    border: "1px solid #c0c0c0",
    borderRadius: "4px",
    fontSize: "14px",
    backgroundColor: "#fff",
    cursor: "pointer",
    ":focus": {
      outline: "none",
      borderColor: "#007bff",
      boxShadow: "0 0 0 2px rgba(0, 123, 255, 0.25)",
    },
  },
  testcaseOptions: {
    maxHeight: "220px",
    overflowY: "auto",
    border: "1px solid #ddd",
    borderRadius: "4px",
    backgroundColor: "#fff",
  },
  testcaseOption: {
    display: "block",
    width: "100%",
    padding: "8px 12px",
    border: "none",
    borderBottom: "1px solid #e8e8e8",
    backgroundColor: "#fff",
    color: "#333",
    fontSize: "13px",
    textAlign: "left",
    cursor: "pointer",
    ":last-child": { borderBottom: "none" },
    ":hover": { backgroundColor: "#1976d2", color: "#fff" },
  },
  selectedOption: { backgroundColor: "#1976d2", color: "#fff" },
  label: {
    display: "block",
    marginBottom: "6px",
    fontWeight: 600,
    fontSize: "13px",
    color: "#333",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  section: {
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: "1px solid #eee",
  },
  lastSection: { borderBottom: "none", marginBottom: 0, paddingBottom: 0 },
  results: {
    maxHeight: "220px",
    overflowY: "auto",
    border: "1px solid #ddd",
    borderRadius: "4px",
    backgroundColor: "#fafafa",
  },
  resultItem: {
    padding: "10px 12px",
    cursor: "pointer",
    borderBottom: "1px solid #e8e8e8",
    fontSize: "13px",
    fontFamily: "monospace",
    backgroundColor: "#fff",
    color: "#333",
    transition: "background-color 0.15s ease, color 0.15s ease",
    ":hover": { backgroundColor: "#1976d2", color: "#ffffff" },
  },
  lastResultItem: { borderBottom: "none" },
  noResults: {
    padding: "16px",
    color: "#888",
    fontStyle: "italic",
    textAlign: "center",
    backgroundColor: "#f9f9f9",
    borderRadius: "4px",
  },
  paramsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  paramItem: { marginBottom: 0 },
  paramLabel: {
    display: "block",
    marginBottom: "4px",
    fontWeight: 500,
    fontSize: "11px",
    color: "#666",
    textTransform: "capitalize",
  },
  paramSelect: { marginBottom: 0 },
});

ExtendedSearchDropdown.propTypes = {
  /** The testplan report object */
  report: PropTypes.object,
  /** Callback when navigating to a permutation */
  onNavigate: PropTypes.func.isRequired,
  /** Callback to close the dropdown */
  onClose: PropTypes.func.isRequired,
  /** Callback to filter report (like search) */
  handleNavFilter: PropTypes.func,
  /** Current selection state */
  value: PropTypes.shape({
    selectedTest: PropTypes.string,
    selectedTestsuite: PropTypes.string,
    selectedTestcase: PropTypes.string,
    selectedParams: PropTypes.object,
    searchText: PropTypes.string,
  }).isRequired,
  /** Callback to update selection state */
  onStateChange: PropTypes.func.isRequired,
  /** Ref to the button that toggles the dropdown */
  triggerRef: PropTypes.shape({ current: PropTypes.any }),
};

export default ExtendedSearchDropdown;

export {
  collectTestcases,
  paramValueToken,
  getUniqueField,
  buildFilterOptions,
  applyParamFilters,
};
