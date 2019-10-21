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
import {
  UpdateSelectedState,
  GetReportState,
  GetCenterPane,
} from './reportUtils.js';
import {ReportToNavEntry} from "../Common/utils";

/**
 * Interactive report viewer. As opposed to a batch report, an interactive
 * report starts off with no test results and fills up with results as
 * the tests are run interactively. Tests can be run by clicking buttons in
 * the UI.
 */
class InteractiveReport extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      report: null,
      selected: [],
      assertions: null,
      loading: false,
      error: null,
    };
    this.runEntry = this.runEntry.bind(this);
    this.setEntryStatus = this.setEntryStatus.bind(this);
    this.setEntryStatusRecur = this.setEntryStatusRecur.bind(this);
    this.handleNavClick = this.handleNavClick.bind(this);
    this.handlePlayClick = this.handlePlayClick.bind(this);
  }

  /**
   * Fetch the Testplan report once the component has mounted.
   * @public
   */
  componentDidMount() {
    this.setState({loading: true}, this.getReport);
  }

  /**
   * Fetch the Testplan interactive report.
   *
   * Currently we don't make a real API call and instead just display a fake
   * report.
   */
  getReport() {
    setTimeout(
      () => this.setState({
        report: FakeInteractiveReport,
        selected: this.autoSelect(FakeInteractiveReport),
        loading: false,
      }),
      1500,
    );
  }

  /**
   * Auto-select an entry in the report when it is first loaded.
   */
  autoSelect(reportEntry) {
    return [ReportToNavEntry(reportEntry)];
  }

  /**
   * Trigger the run of either a single testcase or a group of testcases
   * (suite, MultiTest or Testplan) represented by an entry in the report.
   */
  runEntry(selectedEntries) {
    this.setEntryStatus(selectedEntries, "running");
    // Normally would make request to the backend here to run the test. For now,
    // we'll mock out the backend interaction and just wait a set time before
    // marking the test as finished.
    setTimeout(() => this.setEntryStatus(selectedEntries, "passed"), 3000);
  }

  /**
   * Update the status of an entry in the report. We completely re-create the
   * report tree instead of mutating the existing report object.
   */
  setEntryStatus(selectedEntries, newStatus) {
    this.setState((state, props) => ({
        report: this.setEntryStatusRecur(
          state.report,
          selectedEntries,
          newStatus,
        ),
    }));
  }

  /**
   * Traverses the report tree recursively and updates the matching entry
   * state to be "running".
   *
   * Since we know the hierarchy of selected elements we can restrict ourselves
   * to only searching branches that contain the updated entry. Other branches
   * (i.e. other MultiTests or suites that don't contain a particular
   * testcase) are left as they are.
   *
   * @param {object} currEntry - the current report entry to check recursively.
   * @param {array} selectedEntries - an array of the currently selected
   *   report entry hierarchy, from highest to lowest. Initially, the highest
   *   entry will always be the root Testplan object but this will shift with
   *   every recursive call. The lowest (last) entry in the array will always
   *   be whichever element we are updating the entry status for.
   * @param {string} newStatus - the new status to set on the entry we are
   *   updating.
   */
  setEntryStatusRecur(currEntry, selectedEntries, newStatus) {
    const [headSelectedEntry, ...tailSelectedEntries] = selectedEntries;
    const match = (currEntry.uid === headSelectedEntry.uid);

    // Check if the UID matches.
    if (match) {
      // Two cases to distinguish between:
      //
      // - There are more selected entries to search down for: we leave the
      //   status of the current element unchanged and recurse down.
      // - There are no more selected entries: we have found the element to
      //   update, so update its status and stop recursion.
      if (tailSelectedEntries.length === 0) {
        return {
          ...currEntry,
          status: newStatus,
        };
      } else {
        return {
          ...currEntry,
          entries: currEntry.entries.map(
            (entry) => this.setEntryStatusRecur(
              entry,
              tailSelectedEntries,
              newStatus,
            )
          ),
        };
      }
    } else {
      // If there is no UID match then we are in the wrong branch. Return
      // the entry unchanged.
      return currEntry;
    }
  }

  /**
   * Handle a navigation entry being clicked. Update the current selection
   * state and displayed assertions.
   */
  handleNavClick(e, entry, depth) {
    e.stopPropagation();
    this.setState((state, props) => UpdateSelectedState(state, entry, depth));
  }

  /* Handle the play button being clicked on a Nav entry. */
  handlePlayClick(e, navEntry) {
    e.stopPropagation();
    const currSelected = this.state.selected[this.state.selected.length - 1];
    if (!currSelected) {
      alert(
        "Error: Expected a report element to be selected. Selected = " +
        this.state.selected
      );
      return;
    }

    const fullSelected = this.state.selected.concat([navEntry]);
    this.runEntry(fullSelected);
  }

  render() {
    const noop = () => undefined;
    const {reportStatus, reportFetchMessage} = GetReportState(this.state);
    const centerPane = GetCenterPane(
      this.state,
      this.props,
      reportFetchMessage,
      null,
    );


    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          status={reportStatus}
          handleNavFilter={noop}
          updateFilterFunc={noop}
          updateEmptyDisplayFunc={noop}
          updateTagsDisplayFunc={noop}
        />
        <InteractiveNav
          report={this.state.report}
          selected={this.state.selected}
          filter={null}
          displayEmpty={true}
          displayTags={false}
          handleNavClick={this.handleNavClick}
          handlePlayClick={this.handlePlayClick}
        />
        {centerPane}
      </div>
    );
  }
}

const styles = StyleSheet.create({interactiveReport: {}});

export default InteractiveReport;

