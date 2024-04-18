import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";

import BasicAssertion from "../BasicAssertion";

function propsEqual() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:42.795536+00:00",
      description: null,
      line_no: 25,
      label: "==",
      second: "foo",
      meta_type: "assertion",
      passed: true,
      type: "Equal",
      utc_time: "2019-02-12T17:41:42.795530+00:00",
      first: "foo",
    },
  };
}

function propsHighlightEqual() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:42.795536+00:00",
      description: "compare two string",
      line_no: 25,
      label: "==",
      second: "This is a short thing",
      meta_type: "assertion",
      passed: false,
      type: "Equal",
      utc_time: "2019-02-12T17:41:42.795530+00:00",
      first: "This is a long thing with some extra at the end",
      type_actual: "str",
      type_expected: "str",
    },
  };
}

function propsNotEqual() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.021937+00:00",
      description: null,
      line_no: 30,
      label: "!=",
      second: "bar",
      meta_type: "assertion",
      passed: true,
      type: "NotEqual",
      utc_time: "2019-02-12T17:41:43.021930+00:00",
      first: "foo",
    },
  };
}

function propsGreater() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.023470+00:00",
      description: null,
      line_no: 31,
      label: ">",
      second: 2,
      meta_type: "assertion",
      passed: true,
      type: "Greater",
      utc_time: "2019-02-12T17:41:43.023464+00:00",
      first: 5,
    },
  };
}

function propsGreaterEqual() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.025466+00:00",
      description: null,
      line_no: 32,
      label: ">=",
      second: 2,
      meta_type: "assertion",
      passed: true,
      type: "GreaterEqual",
      utc_time: "2019-02-12T17:41:43.025459+00:00",
      first: 2,
    },
  };
}

function propsLess() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.028544+00:00",
      description: null,
      line_no: 34,
      label: "<",
      second: 20,
      meta_type: "assertion",
      passed: true,
      type: "Less",
      utc_time: "2019-02-12T17:41:43.028537+00:00",
      first: 10,
    },
  };
}

function propsLessEqual() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.029897+00:00",
      description: null,
      line_no: 35,
      label: "<=",
      second: 10,
      meta_type: "assertion",
      passed: true,
      type: "LessEqual",
      utc_time: "2019-02-12T17:41:43.029890+00:00",
      first: 10,
    },
  };
}

function propsIsClose() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.042097+00:00",
      description: null,
      abs_tol: 0,
      line_no: 50,
      rel_tol: 0.1,
      label: "~=",
      second: 95,
      meta_type: "assertion",
      passed: true,
      type: "IsClose",
      utc_time: "2019-02-12T17:41:43.042090+00:00",
      first: 100,
    },
  };
}

function propsLog() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.045339+00:00",
      description: null,
      line_no: 56,
      meta_type: "entry",
      message:
        "This is a log message, it will be displayed along with other assertion details.",
      type: "Log",
      utc_time: "2019-02-12T17:41:43.045333+00:00",
    },
  };
}

function propsIsTrue() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.046710+00:00",
      description: "Boolean Truthiness check",
      expr: true,
      line_no: 61,
      meta_type: "assertion",
      passed: true,
      type: "IsTrue",
      utc_time: "2019-02-12T17:41:43.046704+00:00",
    },
  };
}

function propsIsFalse() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.048126+00:00",
      description: "Boolean Falseness check",
      expr: false,
      line_no: 62,
      meta_type: "assertion",
      passed: true,
      type: "IsFalse",
      utc_time: "2019-02-12T17:41:43.048120+00:00",
    },
  };
}

function propsFail() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.049460+00:00",
      description: "This is an explicit failure.",
      line_no: 64,
      meta_type: "assertion",
      passed: false,
      type: "Fail",
      utc_time: "2019-02-12T17:41:43.049454+00:00",
    },
  };
}

function propsContain() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.050888+00:00",
      container: "foobar",
      description: "Passing membership",
      line_no: 67,
      member: "foo",
      meta_type: "assertion",
      passed: true,
      type: "Contain",
      utc_time: "2019-02-12T17:41:43.050882+00:00",
    },
  };
}

function propsNotContain() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.052594+00:00",
      container: "{'a': 1, 'b': 2}",
      description: "Failing membership",
      line_no: 71,
      member: 10,
      meta_type: "assertion",
      passed: true,
      type: "NotContain",
      utc_time: "2019-02-12T17:41:43.052579+00:00",
    },
  };
}

function propsEqualSlices() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.053943+00:00",
      actual: [1, 2, 3, 4, 5, 6, 7, 8],
      description: "Comparison of slices",
      data: [
        ["slice(2, 4, None)", [2, 3], [], [3, 4], [3, 4]],
        ["slice(6, 8, None)", [6, 7], [], [7, 8], [7, 8]],
      ],
      line_no: 79,
      included_indices: [],
      meta_type: "assertion",
      passed: true,
      expected: ["a", "b", 3, 4, "c", "d", 7, 8],
      type: "EqualSlices",
      utc_time: "2019-02-12T17:41:43.053936+00:00",
    },
  };
}

function propsEqualExcludeSlices() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.055991+00:00",
      actual: [1, 2, 3, 4, 5, 6, 7, 8],
      description: "Comparison of slices (exclusion)",
      data: [
        [
          "slice(0, 2, None)",
          [2, 3, 4, 5, 6, 7],
          [4, 5, 6, 7],
          [3, 4, 5, 6, 7, 8],
          [3, 4, "c", "d", "e", "f"],
        ],
        [
          "slice(4, 8, None)",
          [0, 1, 2, 3],
          [0, 1],
          [1, 2, 3, 4],
          ["a", "b", 3, 4],
        ],
      ],
      line_no: 91,
      included_indices: [2, 3],
      meta_type: "assertion",
      passed: true,
      expected: ["a", "b", 3, 4, "c", "d", "e", "f"],
      type: "EqualExcludeSlices",
      utc_time: "2019-02-12T17:41:43.055984+00:00",
    },
  };
}

function propsLineDiff() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.057544+00:00",
      ignore_space_change: false,
      description: null,
      unified: false,
      type: "LineDiff",
      line_no: 98,
      second: ["abc\n", "xyz\n", "\n"],
      meta_type: "assertion",
      context: false,
      ignore_whitespaces: false,
      delta: [],
      ignore_blank_lines: true,
      passed: true,
      utc_time: "2019-02-12T17:41:43.057524+00:00",
      first: ["abc\n", "xyz\n"],
    },
  };
}

function propsExceptionRaised() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.112284+00:00",
      description: null,
      exception_match: true,
      pattern: null,
      line_no: 112,
      expected_exceptions: ["KeyError"],
      meta_type: "assertion",
      raised_exception: ["<type 'exceptions.KeyError'>", "'bar'"],
      func: null,
      type: "ExceptionRaised",
      func_match: true,
      passed: true,
      utc_time: "2019-02-12T17:41:43.112279+00:00",
      pattern_match: true,
    },
  };
}

function propsExceptionNotRaised() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.117589+00:00",
      description: null,
      exception_match: false,
      pattern: null,
      line_no: 146,
      expected_exceptions: ["TypeError"],
      meta_type: "assertion",
      raised_exception: ["<type 'exceptions.KeyError'>", "'bar'"],
      func: null,
      type: "ExceptionNotRaised",
      func_match: true,
      passed: true,
      utc_time: "2019-02-12T17:41:43.117579+00:00",
      pattern_match: true,
    },
  };
}

function propsDictCheck() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.300822+00:00",
      description: null,
      has_keys: ["foo", "alpha"],
      line_no: 570,
      meta_type: "assertion",
      absent_keys_diff: ["bar"],
      passed: false,
      has_keys_diff: ["alpha"],
      type: "DictCheck",
      absent_keys: ["bar", "beta"],
      utc_time: "2019-02-12T17:41:43.300815+00:00",
    },
  };
}

function propsDictCheckWithoutCheckingAbsent() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.311722+00:00",
      description: null,
      has_keys: ["foo", "alpha"],
      line_no: 570,
      meta_type: "assertion",
      absent_keys_diff: [],
      passed: false,
      has_keys_diff: ["alpha"],
      type: "DictCheck",
      absent_keys: [],
      utc_time: "2019-02-12T17:41:43.312097+00:00",
    },
  };
}

function propsFixCheck() {
  return {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.312797+00:00",
      description: null,
      has_keys: [26, 22, 11],
      line_no: 675,
      meta_type: "assertion",
      absent_keys_diff: [555],
      passed: false,
      has_keys_diff: [26, 11],
      type: "FixCheck",
      absent_keys: [444, 555],
      utc_time: "2019-02-12T17:41:43.312789+00:00",
    },
  };
}

describe("BasicAssertion", () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = {};
    shallowComponent = undefined;
  });

  it("shallow renders the Equal assertion", () => {
    props = propsEqual();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the highlight Equal assertion", () => {
    props = propsHighlightEqual();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the NotEqual assertion", () => {
    props = propsNotEqual();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the Greater assertion", () => {
    props = propsGreater();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the GreaterEqual assertion", () => {
    props = propsGreaterEqual();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the Less assertion", () => {
    props = propsLess();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the LessEqual assertion", () => {
    props = propsLessEqual();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the IsClose assertion", () => {
    props = propsIsClose();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the Log assertion", () => {
    props = propsLog();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the IsTrue assertion", () => {
    props = propsIsTrue();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the IsFalse assertion", () => {
    props = propsIsFalse();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the Fail assertion", () => {
    props = propsFail();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the Contain assertion", () => {
    props = propsContain();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the NotContain assertion", () => {
    props = propsNotContain();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the EqualSlices assertion", () => {
    props = propsEqualSlices();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the EqualExcludeSlices assertion", () => {
    props = propsEqualExcludeSlices();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the LineDiff assertion", () => {
    props = propsLineDiff();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the ExceptionRaised assertion", () => {
    props = propsExceptionRaised();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the ExceptionNotRaised assertion", () => {
    props = propsExceptionNotRaised();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the DictCheck assertion", () => {
    props = propsDictCheck();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the DictCheck assertion which has no absent key", () => {
    props = propsDictCheckWithoutCheckingAbsent();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders the FixCheck assertion", () => {
    props = propsFixCheck();
    shallowComponent = shallow(<BasicAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
