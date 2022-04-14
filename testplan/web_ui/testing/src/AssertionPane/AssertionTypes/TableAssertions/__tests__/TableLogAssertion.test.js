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


function advancedTableProps() {
  return {
    assertion: {
      "flag": "DEFAULT",
      "machine_time": "2021-06-25T16:06:10.622340+00:00",
      "line_no": 92,
      "display_index": false,
      "description": "table log assertion",
      "table": [
        [
          "External Link",
          {
            "link": "https://www.google.com",
            "title": "Google",
            "new_window": true,
            "inner": false,
            "type": "link"
          }
        ],
        [
          "Internal Link",
          {
            "link": "/",
            "title": "Home",
            "new_window": true,
            "inner": true,
            "type": "link"
          }
        ],
        [
          "Formatted Value - 0.6",
          {
            "value": 0.6,
            "display": "60%",
            "type": "formattedValue"
          }
        ],
        [
          "Formatted Value - 0.08",
          {
            "value": 0.08,
            "display": "8%",
            "type": "formattedValue"
          }
        ]
      ],
      "columns": [
        "Description",
        "Data"
      ],
      "meta_type": "entry",
      "category": "DEFAULT",
      "type": "TableLog",
      "indices": [
        0,
        1,
        2,
        3
      ],
      "utc_time": "2021-06-25T08:06:10.622331+00:00"
    }
  }
}

describe('TableLogAssertion', () => {
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    shallowComponent = undefined;
  });

  it('shallow renders the table log HTML structure', () => {
    let props = defaultProps();
    shallowComponent = shallow(<TableLogAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });

  it('shallow renders the advanced table log HTML structure', () => {
    let props = advancedTableProps();
    shallowComponent = shallow(<TableLogAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});