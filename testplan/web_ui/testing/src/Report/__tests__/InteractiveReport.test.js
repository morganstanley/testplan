/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';

import InteractiveReport from '../InteractiveReport';

describe('InteractiveReport', () => {
  it("shallow renders and matches snapshot", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    expect(interactiveReport).toMatchSnapshot();
  });
});

