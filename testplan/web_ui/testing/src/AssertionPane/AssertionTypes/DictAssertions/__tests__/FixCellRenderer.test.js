import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import FixCellRenderer from '../FixCellRenderer';

function defaultProps() {
  return {};
}

function valueProps() {
  return {
    "value":{"value":"B","type":"B"},
    "data":{
      "descriptor":{
        "lineNo":667,
        "isFix":true,
        "indent":1,
        "isListKey":false,
        "isFailed":true
      },
      "key":{
        "value":601,
        "type":"key"
      },
      "value":{
        "value":"A",
        "type":"str"
      },
      "expected":{
        "value":"B",
        "type":"B"
      }
    },
    "colDef":{
      "headerName":"Expected",
      "field":"expected"
    }
  };
}


describe('DictLogAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    shallowComponent = undefined;
  });

  it('shallow renders the dict value', () => {
    props = valueProps();
    shallowComponent = shallow(<FixCellRenderer {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
  
});