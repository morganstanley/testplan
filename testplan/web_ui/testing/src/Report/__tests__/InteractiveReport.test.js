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
    const reportState = interactiveReport.state("report");
    const selectedEntries = [
      reportState,
      reportState.entries[0],
      reportState.entries[0].entries[0],
      reportState.entries[0].entries[0].entries[0],
    ];
    interactiveReport.instance().setEntryStatus(selectedEntries, "passed");
    interactiveReport.update();

    const newTestcaseEntry = (
      interactiveReport.state("report").entries[0].entries[0].entries[0]
    );
    expect(newTestcaseEntry.status).toBe("passed");
    expect(interactiveReport).toMatchSnapshot();
  });
});

