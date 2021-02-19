import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import XYGraphAssertion from '../XYGraphAssertion.js';

function defaultProps() {
  return {
    assertion: {
                "meta_type": "entry",
                "utc_time": "2019-07-12T12:36:09.782759+00:00",
                "machine_time": "2019-07-12T12:36:09.782759+00:00",
                "type": "Graph",
                "series_options": {
                                     'Data Name': {"colour": "red"}
                                  },
                "line_no": 50,
                "graph_data": {
                    "Data Name": [{
                            "x": "A",
                            "y": 10
                        }, {
                            "x": "B",
                            "y": 5
                        }, {
                            "x": "C",
                            "y": 15
                        }
                    ]
                },
                "description": "Bar Graph",
                "category": "DEFAULT",
                "graph_options": {"legend": true},
                "graph_type": "Bar"
            }
    };
}


describe('XYGraphAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('can render basic markup without error', () => {
    shallow(<XYGraphAssertion {...props}/>).html();
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<XYGraphAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });

});