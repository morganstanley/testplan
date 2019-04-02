import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import SortButtonGroup from '../SortButtonGroup';

function defaultProps() {
  return {
    uid: 'sort-test-uid',
    defaultSortType: 3,
    sortTypeList: [1, 2, 3, 4],
    flattenedDict: [
      [0,"foo","Passed",["int","1"],["int","1"]],
      [0,"bar","Failed",["int","2"],["int","5"]],
      [0,"extra-key","Failed",[null,"ABSENT"],["int","10"]]
    ],
    setRowData: jest.fn()
  };
}

describe('DictLogAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = {};
    shallowComponent = undefined;
  });

  it('shallow renders SortButtonGroup component', () => {
    props = defaultProps();
    shallowComponent = shallow(<SortButtonGroup {...props} />);
    expect(shallowComponent).toMatchSnapshot();
  });
});