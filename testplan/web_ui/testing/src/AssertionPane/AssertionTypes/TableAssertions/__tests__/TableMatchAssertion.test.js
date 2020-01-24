import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import TableMatchAssertion from '../TableMatchAssertion';

function defaultProps() {
  return {
    assertion: {
      "category":"DEFAULT",
      "machine_time":"2019-02-12T17:41:43.176922+00:00",
      "description":"Table Match: list of list vs list of list",
      "exclude_columns":null,
      "report_fails_only":false,
      "fail_limit":0,
      "line_no":284,
      "data":[
        [0,["Bob",32],{},{},{}],
        [1,["Susan",24],{},{},{}],
        [2,["Rick",67],{},{},{}]
      ],
      "strict":false,
      "meta_type":"assertion",
      "columns":["name","age"],
      "passed":true,
      "include_columns":null,
      "message":null,
      "type":"TableMatch",
      "utc_time":"2019-02-12T17:41:43.176916+00:00"
    }
  };
}


describe('FixMatchAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<TableMatchAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});