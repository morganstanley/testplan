/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';

import InteractiveReport from '../InteractiveReport.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';
import {ReportToNavEntry} from '../../Common/utils.js';

describe('InteractiveReport', () => {
  it("shallow renders and matches snapshot", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    expect(interactiveReport).toMatchSnapshot();
  });

  it("updates testcase status to passed", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({report: FakeInteractiveReport});

    const selectedReportEntries = [
      FakeInteractiveReport,
      FakeInteractiveReport.entries[0],
      FakeInteractiveReport.entries[0].entries[0],
      FakeInteractiveReport.entries[0].entries[0].entries[0],
    ];

    const selectedNavEntries = selectedReportEntries.map(ReportToNavEntry);
    interactiveReport.instance().setEntryStatus(selectedNavEntries, "passed");
    interactiveReport.update();

    const newTestcaseEntry = (
      interactiveReport.state("report").entries[0].entries[0].entries[0]
    );
    expect(newTestcaseEntry.status).toBe("passed");
    expect(interactiveReport).toMatchSnapshot();
  });
});

