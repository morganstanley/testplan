import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import { RegexAssertion, RegexMatchLineAssertion } from "../RegexAssertions";

const RegexMatchInputs = [
  {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.145337+00:00",
      description: "string pattern match",
      pattern: "foo",
      line_no: 196,
      meta_type: "assertion",
      passed: true,
      match_indexes: [[0, 3]],
      type: "RegexMatch",
      utc_time: "2019-02-12T17:41:43.145332+00:00",
      string: "foobar",
    },
  },
  {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.150042+00:00",
      description: null,
      pattern: "baz",
      line_no: 217,
      meta_type: "assertion",
      passed: true,
      match_indexes: [],
      type: "RegexMatchNotExists",
      utc_time: "2019-02-12T17:41:43.150037+00:00",
      string: "foobar",
    },
  },
  {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.153301+00:00",
      description: null,
      pattern: "second",
      line_no: 225,
      meta_type: "assertion",
      passed: true,
      match_indexes: [[11, 17]],
      type: "RegexSearch",
      utc_time: "2019-02-12T17:41:43.153294+00:00",
      string: "first line\nsecond line\nthird line",
    },
  },
  {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.154688+00:00",
      description: "Passing search empty",
      pattern: "foobar",
      line_no: 230,
      meta_type: "assertion",
      passed: true,
      match_indexes: [],
      type: "RegexSearchNotExists",
      utc_time: "2019-02-12T17:41:43.154681+00:00",
      string: "first line\nsecond line\nthird line",
    },
  },
  {
    assertion: {
      category: "DEFAULT",
      machine_time: "2019-02-12T17:41:43.157637+00:00",
      description: null,
      string: "foo foo foo bar bar foo bar",
      pattern: "foo",
      line_no: 243,
      condition_match: true,
      meta_type: "assertion",
      condition: "<lambda>",
      passed: true,
      type: "RegexFindIter",
      utc_time: "2019-02-12T17:41:43.157630+00:00",
      match_indexes: [
        [0, 3],
        [4, 7],
        [8, 11],
        [20, 23],
      ],
    },
  },
];

describe("RegexAssertions", () => {
  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
  });

  it.each(RegexMatchInputs)("shallow renders $assertion.type", (props) => {
    const shallowComponent = shallow(<RegexAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });

  it("shallow renders RegexMatchLineAssertion", () => {
    const props = {
      assertion: {
        category: "DEFAULT",
        machine_time: "2019-02-12T17:41:43.160987+00:00",
        description: null,
        string: "first line\nsecond line\nthird line",
        pattern: "\\w+ line$",
        line_no: 257,
        meta_type: "assertion",
        passed: true,
        type: "RegexMatchLine",
        utc_time: "2019-02-12T17:41:43.160981+00:00",
        match_indexes: [
          [0, 0, 10],
          [1, 0, 11],
          [2, 0, 10],
        ],
      },
    };
    const shallowComponent = shallow(<RegexMatchLineAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
