import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import DiscreteChartAssertion from '../DiscreteChartAssertion.js';

function defaultProps() {
  return {
    assertion: {
                "meta_type": "entry",
                "utc_time": "2019-07-12T12:36:09.796381+00:00",
                "machine_time": "2019-07-12T12:36:09.796381+00:00",
                "type": "DiscreteChart",
                "series_options": {
                    "Data Name": {
                        "colour": "literal"
                    }
                },
                "line_no": 101,
                "graph_data": {
                    "Data Name": [{
                            "angle": 1,
                            "color": "#89DAC1",
                            "name": "green"
                        }, {
                            "angle": 2,
                            "color": "#F6D18A",
                            "name": "yellow"
                        }, {
                            "angle": 5,
                            "color": "#1E96BE",
                            "name": "cyan"
                        }, {
                            "angle": 3,
                            "color": "#DA70BF",
                            "name": "magenta"
                        }, {
                            "angle": 5,
                            "color": "#F6D18A",
                            "name": "yellow again"
                        }
                    ]
                },
                "description": "Pie Chart",
                "category": "DEFAULT",
                "graph_options": null,
                "graph_type": "Pie"
            }
    };
}


describe('DiscreteChartAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('can render basic markup without error', () => {
    shallow(<DiscreteChartAssertion {...props}/>).html();
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<DiscreteChartAssertion {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });

});