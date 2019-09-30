/* Tests the EmptyReport component. */
import React from 'react';
import {shallow} from 'enzyme';

import EmptyReport from '../EmptyReport';

describe('EmptyReport', () => {
  it("shallow renders and matches snapshot", () => {
    const emptyReport = shallow(<EmptyReport />);
    expect(emptyReport).toMatchSnapshot();
  });

  it("renders a custom error message", () => {
    const errorReport = shallow(<EmptyReport message="418 I'm a teapot" />);
    expect(errorReport).toMatchSnapshot();
  });
});

