/**
 * Constants used across the entire application.
 */
const GREEN = '#228F1D';
const RED = '#A2000C';
const LIGHT_GREY = '#F3F3F3';
const MEDIUM_GREY = '#D0D0D0';
const DARK_GREY = '#ADADAD';

const COLUMN_WIDTH = 18;

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
  'suite': 'suite',
  'cppunit-suite': 'suite',
  'boost-test-suite': 'suite',
  'gtest-suite': 'suite',
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
  'suite': 'S',
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
  'suite',
  'parametrization',
  'testcase',
];

const STATUS = [
  'passed',
  'failed',

  // The following statuses only apply to interactive mode. TODO: maybe create
  // a new INTERACTIVE_STATUS enum?
  'ready',
  'running',
];

const NAV_ENTRY_DISPLAY_DATA = [
  'name',
  'uid',
  'type',
  'category',
  'status',
  'case_count',
  'tags',
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

export {
  GREEN,
  RED,
  LIGHT_GREY,
  MEDIUM_GREY,
  DARK_GREY,
  COLUMN_WIDTH,
  INDENT_MULTIPLIER,
  TOOLBAR_BUTTONS_BATCH,
  TOOLBAR_BUTTONS_INTERACTIVE,
  CATEGORIES,
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS,
  NAV_ENTRY_DISPLAY_DATA,
  BASIC_ASSERTION_TYPES,
  SORT_TYPES,
  DICT_GRID_STYLE,
};
