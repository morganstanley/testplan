import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import MarkdownAssertion from '../MarkdownAssertion';

function defaultProps() {
  return {
    assertion: {
      "category": "DEFAULT",
      "machine_time": "2019-02-12T17:41:43.302500+00:00",
      "description": null,
      "message": "Markdown Test [Github](https://github.com/Morgan-Stanley/testplan)\n Test",
      "line_no": 123,
      "meta_type": "entry",
      "type": "Markdown",
      "utc_time": "2019-02-12T17:41:43.302494+00:00"
    }
  };
}


describe('MarkdownAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<MarkdownAssertion {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});
