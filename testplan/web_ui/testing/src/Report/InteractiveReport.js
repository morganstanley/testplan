/**
 * InteractiveReport: Renders an Interactive report, which is used to control
 * test environments and run tests interactively. Requires the Testplan
 * interactive API backend to be running.
 */
import React from 'react';
import {StyleSheet, css} from 'aphrodite';

import Toolbar from '../Toolbar/Toolbar.js';
import InteractiveNav from '../Nav/InteractiveNav.js';
import {FakeInteractiveReport} from '../Common/sampleReports.js';

/**
 * Interactive report viewer. As opposed to a batch report, an interactive
 * report starts off with no test results and fills up with results as
 * the tests are run interactively. Tests can be run by clicking buttons in
 * the UI.
 */
class InteractiveReport extends React.Component {

  constructor(props) {
    super(props);
    this.state = {report: FakeInteractiveReport};
    this.runEntry = this.runEntry.bind(this);
    this.setEntryStatus = this.setEntryStatus.bind(this);
    this.setEntryStatusRecur = this.setEntryStatusRecur.bind(this);
  }

  /**
   * Trigger the run of either a single testcase or a group of testcases
   * (suite, MultiTest or Testplan) represented by an entry in the report.
   */
  runEntry(entry) {
    this.setEntryStatus(entry, "running");
    // Normally would make request to the backend here to run the test. For now,
    // we'll mock out the backend interaction and just wait a set time before
    // marking the test as finished.
    setTimeout(() => this.setEntryStatus(entry, "passed"), 3000);
  }

  /**
   * Update the status of an entry in the report. We completely re-create the
   * report tree instead of mutating the existing report.
   */
  setEntryStatus(entry, newStatus) {
    this.setState((state, props) => ({
        report: this.setEntryStatusRecur(state.report, entry, newStatus),
    }));
  }

  /**
   * Traverses the report tree recursively and updates the matching entry
   * state to be "running".
   *
   * Note that this implementation is very simplistic in the interst of getting
   * a basic MVP interactive mode - we check and update every single entry in
   * the report, so it its complexity is O(n) in the total number of entries in
   * the report. For a very large report this could be inefficient. As a future
   * optimization we could skip checking unnecessary branches if we can know
   * which parent entries (multitest or suite) the entry we are searching for
   * belongs to - reducing the search complexity to O(log(n)).
   */
  setEntryStatusRecur(currEntry, runningEntry, newStatus) {
    const match = (currEntry.uid === runningEntry.uid);
    return {
      ...currEntry,
      status: match ? newStatus : currEntry.status,
      entries: currEntry.entries.map(
        (entry) => this.setEntryStatusRecur(entry, runningEntry, newStatus)
      ),
    };
  }

  render() {
    const noop = () => undefined;

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          status={undefined}
          handleNavFilter={noop}
          updateFilterFunc={noop}
          updateEmptyDisplayFunc={noop}
          updateTagsDisplayFunc={noop}
        />
        <InteractiveNav
          report={[this.state.report]}
          saveAssertions={noop}
          filter={undefined}
          displayEmpty={true}
          displayTags={false}
          runEntry={this.runEntry}
        />
      </div>
    );
  }
}

const styles = StyleSheet.create({interactiveReport: {}});

export default InteractiveReport;

