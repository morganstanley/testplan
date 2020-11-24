import React from 'react';
import {shallow, mount} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import DictCellRenderer from '../DictCellRenderer';

function defaultProps() {
  return {};
}

function valueProps() {
  return {
    "value": { "value": "BB", "type": "aa" },
    "data": {
      "descriptor": {
        "lineNo": 667,
        "isFix": true,
        "indent": 1,
        "isListKey": false,
        "isFailed": true
      },
      "key": {
        "value": 601,
        "type": "key"
      },
      "value": {
        "value": "A",
        "type": "str"
      },
      "expected": {
        "value": "BB",
        "type": "aa"
      }
    },
    "colDef": {
      "field": "expected"
    }
  };
}

function keyProps() {
  return {
    "value": { "value": "601", "type": "key" },
    "data": {
      "descriptor": {
        "lineNo": 667,
        "isFix": true,
        "indent": 1,
        "isListKey": false,
        "isFailed": true
      },
      "key": {
        "value": 601,
        "type": "key"
      },
      "value": {
        "value": "A",
        "type": "str"
      },
      "expected": { "value": "B", "type": "B" }
    },
    "colDef": {
      "field": "key"
    }
  };
}

describe('DictLogAssertion', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the dict value', () => {
    props = valueProps();
    shallowComponent = shallow(<DictCellRenderer {...props} />);
    expect(shallowComponent.find('span').text().trim()).toBe('BB');
    expect(shallowComponent.find('sub').text().trim()).toBe('aa');
  });

  it('shallow renders the dict key', () => {
    props = keyProps();
    shallowComponent = mount(<DictCellRenderer {...props} />);
    // test css style
    expect(shallowComponent.find('div').prop('style'))
      .toHaveProperty('marginLeft', '1.5rem');
    expect(shallowComponent.find('span').text().trim()).toBe('601')
  });
});