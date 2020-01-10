/**
 * Constants used across the entire application.
 */
const GREEN = '#228F1D';
const RED = '#A2000C';
const ORANGE = '#FFA500';
const LIGHT_GREY = '#F3F3F3';
const MEDIUM_GREY = '#D0D0D0';
const DARK_GREY = '#ADADAD';
const BLACK = '#404040';

const COLUMN_WIDTH = 18;
const INTERACTIVE_COL_WIDTH = 24;  // wider to fit interactive buttons

const INDENT_MULTIPLIER = 1.5;

const TOOLBAR_BUTTONS_BATCH = [
  {name: 'pr', type: 'print'},
  {name: 'if', type: 'info-circle'},
  {name: 'qu', type: 'question-circle'},
  {name: 'fi', type: 'filter'},
  {name: 'ta', type: 'tags'},
  {name: 'ci', type: 'circle'},
  {name: 'jk', type: 'male'},
  {name: 'me', type: 'table'},
  {name: 'mo', type: 'chart-bar'}
];

const TOOLBAR_BUTTONS_INTERACTIVE = [
  {name: 'po', type: 'fa-power-off'},
  {name: 'bg', type: 'fa-bug'},
  {name: 'rf', type: 'fa-refresh'},
  {name: 'pl', type: 'fa-play'},
  {name: 'qu', type: 'fa-question-circle'},
  {name: 'fp', type: 'fa-floppy-o'}
];

const CATEGORIES = {
  'test': 'test',
  'multitest': 'test',
  'cppunit': 'test',
  'gtest': 'test',
  'unittest': 'test',
  'boost-test': 'test',
  'qunit': 'test',
  'testsuite': 'testsuite',
  'cppunit-suite': 'testsuite',
  'boost-test-suite': 'testsuite',
  'gtest-suite': 'testsuite',
  'parametrization': 'parametrization',
  'testcase': 'testcase'
};

const CATEGORY_ICONS = {
  'testplan': 'TP',
  'test': 'T',
  'multitest': 'MT',
  'cppunit': 'CP',
  'gtest': 'GT',
  'unittest': 'UT',
  'boost-test': 'BT',
  'qunit': 'QU',
  'testsuite': 'S',
  'cppunit-suite': 'CS',
  'boost-test-suite': 'BS',
  'gtest-suite': 'GS',
  'parametrization': 'P',
  'testcase': 'C'
};

const ENTRY_TYPES = [
  'testplan',
  'multitest',
  'gtest',
  'boost_test',
  'cppunit',
  'qunit',
  'unittest',
  'testsuite',
  'parametrization',
  'testcase',
];

const STATUS = [
  'error',
  'failed',
  'passed',
  'unstable',
  'unknown',
  'incomplete',
  'skipped',
  'xfail',
  'xpass',
  'xpass-strict',
  'unstable',
  'unknown',
];

const STATUS_CATEGORY = {
  'error': 'error',
  'failed': 'failed',
  'incomplete': 'failed',
  'passed': 'passed',
  'skipped': 'unstable',
  'xfail': 'unstable',
  'xpass': 'unstable',
  'xpass-strict': 'unstable',
  'unstable': 'unstable',
  'unknown': 'unknown',
};

const RUNTIME_STATUS = [
  'ready',
  'running',
  'finished',
];


const NAV_ENTRY_DISPLAY_DATA = [
  'name',
  'uid',
  'type',
  'category',
  'status',
  'runtime_status',
  'counter',
  'tags',
  'parent_uids',
  'logs',
];

const BASIC_ASSERTION_TYPES = [
  'Log',
  'Equal', 'NotEqual', 'Greater', 'GreaterEqual', 'Less', 'LessEqual',
  'IsClose', 'IsTrue', 'IsFalse',
  'Fail', 'Contain', 'NotContain', 'LineDiff',
  'ExceptionRaised', 'ExceptionNotRaised',
  'RegexMatch', 'RegexMatchNotExists', 'RegexSearch', 'RegexSearchNotExists',
  'RegexFindIter', 'RegexMatchLine',
  'XMLCheck',
  'EqualSlices', 'EqualExcludeSlices',
  'DictCheck', 'FixCheck',
  'Attachment', 'MatPlot',
];

const SORT_TYPES = {
  NONE: 0,
  ALPHABETICAL: 1,
  REVERSE_ALPHABETICAL: 2,
  BY_STATUS: 3,
  ONLY_FAILURES: 4,
};

const DICT_GRID_STYLE = {
  MAX_VISIBLE_ROW: 20,
  ROW_HEIGHT: 28,
  EMPTY_ROW_HEIGHT: 5,
  HEADER_HEIGHT: 32,
  BOTTOM_PADDING: 18, // 16 + 2(border 2px)
};

// Interval to poll for report updates over. We may want to reduce this to make
// the UI update more quickly.
//
// NOTE: currently we poll for updates using HTTP for simplicity but in future
// it might be better to use websockets or SSEs to allow the backend to notify
// us when updates are available.
const POLL_MS = 1000;

export {
  GREEN,
  RED,
  ORANGE,
  LIGHT_GREY,
  MEDIUM_GREY,
  DARK_GREY,
  BLACK,
  COLUMN_WIDTH,
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
  NAV_ENTRY_DISPLAY_DATA,
  BASIC_ASSERTION_TYPES,
  SORT_TYPES,
  DICT_GRID_STYLE,
  POLL_MS,
};
