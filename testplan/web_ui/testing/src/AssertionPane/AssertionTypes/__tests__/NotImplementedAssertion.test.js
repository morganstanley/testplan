import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import NotImplementedAssertion from '../NotImplementedAssertion';

function defaultProps() {
  return {
    assertion: {
      "category": "DEFAULT",
      "machine_time": "2019-02-12T17:41:43.302500+00:00",
      "description": null,
      "line_no": 579,
      "meta_type": "entry",
      "type": "Unknown",
      "utc_time": "2019-02-12T17:41:43.302494+00:00"
    }
  };
}


describe('NotImplementedAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<NotImplementedAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});