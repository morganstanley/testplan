/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';

import InteractiveReport from '../InteractiveReport';

describe('InteractiveReport', () => {
  it("shallow renders and matches snapshot", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    expect(interactiveReport).toMatchSnapshot();
  });

  it("updates testcase status to passed", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    const testcaseEntry = (
      interactiveReport.state("report").entries[0].entries[0].entries[0]
    );
    interactiveReport.instance().setEntryStatus(testcaseEntry, "passed");
    interactiveReport.update();

    const newTestcaseEntry = (
      interactiveReport.state("report").entries[0].entries[0].entries[0]
    );
    expect(newTestcaseEntry.status).toBe("passed");
    expect(interactiveReport).toMatchSnapshot();
  });
});

