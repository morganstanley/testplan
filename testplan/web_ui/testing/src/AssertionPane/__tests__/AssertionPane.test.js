import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import AssertionPane from '../AssertionPane';

function defaultProps() {
  return {
    assertions: [
      {
        "category":"DEFAULT",
        "machine_time":"2019-02-12T17:41:42.795536+00:00",
        "description":null,
        "line_no":25,
        "label":"==",
        "second":"foo",
        "meta_type":"assertion",
        "passed":true,
        "type":"Equal",
        "utc_time":"2019-02-12T17:41:42.795530+00:00",
        "first":"foo"
      }
    ],
    left: 19.5,
    testcaseUid: "22758cc5-8a89-472b-bf67-b64dbc2c0b40"
  };
}


describe('AssertionPane', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<AssertionPane {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});