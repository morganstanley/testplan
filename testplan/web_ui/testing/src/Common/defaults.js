/**
 * Constants used across the entire application.
 */

const BLUE = "#e1f0f766";
const DARK_BLUE = "#43aade";
const YELLOW = "#fff17666";
const DARK_YELLOW =  '#ffc107';
const TEAL = '#a7f0dd66';
const DARK_TEAL = "#acebda";
const ROSE = "#fe064466";
const DARK_ROSE = "#be0433";
const GREEN = "#228F1D";
const DARK_GREEN = "#1A721D";
const RED = "#A2000C";
const DARK_RED = "#840008";
const ORANGE = "#D2691E";
const DARK_ORANGE = "#DD8800";
const LIGHT_GREY = "#F3F3F3";
const MEDIUM_GREY = "#D0D0D0";
const DARK_GREY = "#ADADAD";
const BLACK = "#404040";
const NAV_DEFAULT_COLOR = "#6a95c3";

export const BOTTOMMOST_ENTRY_CATEGORY = "testcase";
const COLUMN_WIDTH = 22; // unit: em
const MIN_COLUMN_WIDTH = 180; // unit: px
const INTERACTIVE_COL_WIDTH = 28; // wider to fit interactive buttons

const INDENT_MULTIPLIER = 1.5;

const TOOLBAR_BUTTONS_BATCH = [
  { name: "cl", type: "clock" },
  { name: "pr", type: "print" },
  { name: "if", type: "info-circle" },
  { name: "qu", type: "question-circle" },
  { name: "fi", type: "filter" },
  { name: "ta", type: "tags" },
  { name: "ci", type: "circle" },
  { name: "jk", type: "male" },
  { name: "me", type: "table" },
  { name: "mo", type: "chart-bar" },
];

const TOOLBAR_BUTTONS_INTERACTIVE = [
  { name: "po", type: "fa-power-off" },
  { name: "bg", type: "fa-bug" },
  { name: "rf", type: "fa-refresh" },
  { name: "pl", type: "fa-play" },
  { name: "qu", type: "fa-question-circle" },
  { name: "fp", type: "fa-floppy-o" },
];

const CATEGORIES = {
  test: "test",
  multitest: "test",
  cppunit: "test",
  gtest: "test",
  "boost-test": "test",
  hobbestest: "test",
  pytest: "test",
  pyunit: "test",
  unittest: "test",
  qunit: "test",
  testsuite: "testsuite",
  "cppunit-suite": "testsuite",
  "gtest-suite": "testsuite",
  "boost-test-suite": "testsuite",
  "hobbestest-suite": "testsuite",
  parametrization: "parametrization",
  testcase: "testcase",
  synthesized: "synthesized",
};

const CATEGORY_ICONS = {
  testplan: "TP",
  test: "T",
  multitest: "MT",
  cppunit: "CP",
  gtest: "GT",
  "boost-test": "BT",
  hobbestest: "HT",
  pytest: "PT",
  pyunit: "PU",
  unittest: "UT",
  junit: "JU",
  qunit: "QU",
  testsuite: "S",
  "cppunit-suite": "CS",
  "gtest-suite": "GS",
  "boost-test-suite": "BS",
  "hobbestest-suite": "HS",
  parametrization: "P",
  testcase: "C",
  synthesized: "H",
};

const ENTRY_TYPES = [
  "testplan",
  "multitest",
  "cppunit",
  "gtest",
  "boost_test",
  "unittest",
  "qunit",
  "junit",
  "testsuite",
  "parametrization",
  "testcase",
  "pytest",
  "pyunit",
];

const STATUS = [
  "error",
  "failed",
  "passed",
  "unstable",
  "unknown",
  "incomplete",
  "skipped",
  "xfail",
  "xpass",
  "xpass-strict",
  "unstable",
  "unknown",
];

const STATUS_CATEGORY = {
  error: "error",
  failed: "failed",
  incomplete: "failed",
  passed: "passed",
  skipped: "unstable",
  xfail: "unstable",
  xpass: "unstable",
  "xpass-strict": "unstable",
  unstable: "unstable",
  unknown: "unknown",
};

const RUNTIME_STATUS = [
  "ready",
  "waiting",
  "running",
  "resetting",
  "finished",
  "not_run",
];

const ENV_STATUSES = {
  stopped: "STOPPED",
  starting: "STARTING",
  started: "STARTED",
  stopping: "STOPPING"
};

const NAV_ENTRY_ACTIONS = ["play", "open", "prohibit"];

const NAV_ENTRY_DISPLAY_DATA = [
  "name",
  "uid",
  "type",
  "category",
  "status",
  "runtime_status",
  "counter",
  "tags",
  "parent_uids",
  "logs",
];

const BASIC_ASSERTION_TYPES = [
  "Log",
  "Equal",
  "NotEqual",
  "Greater",
  "GreaterEqual",
  "Less",
  "LessEqual",
  "IsClose",
  "IsTrue",
  "IsFalse",
  "Fail",
  "Contain",
  "NotContain",
  "LineDiff",
  "ExceptionRaised",
  "ExceptionNotRaised",
  "RegexMatch",
  "RegexMatchNotExists",
  "RegexSearch",
  "RegexSearchNotExists",
  "RegexFindIter",
  "RegexMatchLine",
  "XMLCheck",
  "EqualSlices",
  "EqualExcludeSlices",
  "DictCheck",
  "FixCheck",
  "Attachment",
  "MatPlot",
  "RawAssertion",
];

// identifier of radio button
const SORT_TYPES = Object.freeze({
  NONE: Symbol("NONE"),
  ALPHABETICAL: Symbol("ALPHABETICAL"),
  REVERSE_ALPHABETICAL: Symbol("REVERSE_ALPHABETICAL"),
  BY_STATUS: Symbol("BY_STATUS"),
});

// identifier of checkbox
const FILTER_OPTIONS = Object.freeze({
  FAILURES_ONLY: Symbol("FAILURES_ONLY"),
  EXCLUDE_IGNORABLE: Symbol("EXCLUDE_IGNORABLE"),
});

const DICT_GRID_STYLE = {
  MAX_VISIBLE_ROW: 20,
  ROW_HEIGHT: 28,
  EMPTY_ROW_HEIGHT: 5,
  HEADER_HEIGHT: 32,
  BOTTOM_PADDING: 18, // 16 + 2(border 2px)
};

// identifier of expand status
const EXPAND_STATUS = Object.freeze({
  EXPAND: "true",
  COLLAPSE: "false",
  DEFAULT: "default",
});

// Right panel view types
const VIEW_TYPE = Object.freeze({
  ASSERTION: "assertion",
  RESOURCE: "resource",
  DEFAULT: "assertion",
});

// Interval to poll for report updates over. We may want to reduce this to make
// the UI update more quickly.
//
// NOTE: currently we poll for updates using HTTP for simplicity but in future
// it might be better to use websockets or SSEs to allow the backend to notify
// us when updates are available.
const POLL_MS = 1000;

// Fix specification
let defaultFixSpec = { tags: {} };

//log types
const LOG_TYPE = {
  error: "ERROR",
  warning: "WARNING",
};

export {
  BLUE,
  DARK_BLUE,
  YELLOW,
  DARK_YELLOW,
  TEAL,
  DARK_TEAL,
  ROSE,
  DARK_ROSE,
  GREEN,
  DARK_GREEN,
  RED,
  DARK_RED,
  ORANGE,
  DARK_ORANGE,
  LIGHT_GREY,
  MEDIUM_GREY,
  DARK_GREY,
  BLACK,
  NAV_DEFAULT_COLOR,
  COLUMN_WIDTH,
  MIN_COLUMN_WIDTH,
  INTERACTIVE_COL_WIDTH,
  INDENT_MULTIPLIER,
  TOOLBAR_BUTTONS_BATCH,
  TOOLBAR_BUTTONS_INTERACTIVE,
  CATEGORIES,
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS,
  STATUS_CATEGORY,
  RUNTIME_STATUS,
  ENV_STATUSES,
  NAV_ENTRY_ACTIONS,
  NAV_ENTRY_DISPLAY_DATA,
  BASIC_ASSERTION_TYPES,
  SORT_TYPES,
  FILTER_OPTIONS,
  DICT_GRID_STYLE,
  EXPAND_STATUS,
  VIEW_TYPE,
  POLL_MS,
  defaultFixSpec,
  LOG_TYPE,
};
