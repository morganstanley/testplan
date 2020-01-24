import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import ColumnContainAssertion from '../ColumnContainAssertion';

function defaultProps() {
  return {
    assertion:{
      "category":"DEFAULT",
      "machine_time":"2019-02-12T17:41:43.215324+00:00",
      "description":null,
      "column":"symbol",
      "type":"ColumnContain",
      "line_no":454,
      "report_fails_only":false,
      "meta_type":"assertion",
      "limit":null,
      "passed":false,
      "values":["AAPL","AMZN"],
      "data":[
        [0,"AAPL",true],
        [1,"GOOG",false],
        [2,"FB",false],
        [3,"AMZN",true],
        [4,"MSFT",false]
      ],
      "utc_time":"2019-02-12T17:41:43.215318+00:00"
    }
  };
}


describe('DictLogAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<ColumnContainAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});