import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";

import LogGroup from '../LogGroup';

function defaultProps() {
  return {
    logs: [
        {
            "uid":"04b2be21-f14c-4c39-917f-e3e9f7b3eec3",
            "created":"2019-11-28T03:14:37.447875+00:00",
            "funcName":"__exit__",
            "levelno":40,
            "lineno":123,
            "message":"Traceback (most recent call last):\n  File \"testplan.py\", line 123, in _run_testcase(\n        <testplan.testing.multitest.base.MultiTest object at 0x7fb279443320>,\n        <bound method BasicSuite.abc of <__main__.BasicSuite object at 0x7fb279443080>>,\n        None,\n        None,\n        TestCaseReport(name=\"abc\", id=\"abc\", entries=[]))\n    testcase(self.resources, case_result)\n  File \"test_plan.py\", line 16, in abc(<__main__.BasicSuite object at 0x7fb279443080>, Environment[[]], [])\n    print(1/0)\nZeroDivisionError: division by zero",
            "levelname":"ERROR"
        }
    ],
    index: 0,
    onClick: jest.fn()
  };
}


describe('LogGroup', () => {
  let props;
  let shallowComponent;

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    props = defaultProps();
    shallowComponent = undefined;
  });

  it('shallow renders the correct HTML structure', () => {
    shallowComponent = shallow(<LogGroup {...props}/>);
    expect(shallowComponent).toMatchSnapshot();
  });
});
