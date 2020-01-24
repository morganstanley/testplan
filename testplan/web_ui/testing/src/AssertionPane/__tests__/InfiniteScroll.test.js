import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import InfiniteScroll from '../InfiniteScroll';

function defaultProps() {
  return {
    globalIsOpen: false,
    id: "22758cc5-8a89-472b-bf67-b64dbc2c0b40",
    items: [],
    resetGlobalIsOpen: jest.fn()
  };
}


describe('InfiniteScroll', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<InfiniteScroll {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});