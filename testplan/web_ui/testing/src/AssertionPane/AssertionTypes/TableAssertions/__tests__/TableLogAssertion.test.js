import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import TableLogAssertion from '../TableLogAssertion';

function defaultProps() {
  return {
    assertion: {
      "category":"DEFAULT",
      "machine_time":"2019-02-12T17:41:43.241786+00:00",
      "description":"Table Log: list of dicts",
      "line_no":472,
      "display_index":false,
      "meta_type":"entry",
      "columns":["age","name"],
      "indices":[0,1,2],
      "table":[
        {"age":32,"name":"Bob"},
        {"age":24,"name":"Susan"},
        {"age":67,"name":"Rick"}
      ],
      "type":"TableLog",
      "utc_time":"2019-02-12T17:41:43.241777+00:00"
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
    shallowComponent = shallow(<TableLogAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});