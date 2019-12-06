/**
 * InteractiveReport: Renders an Interactive report, which is used to control
 * test environments and run tests interactively. Requires the Testplan
 * interactive API backend to be running.
 */
import React from 'react';
import {StyleSheet, css} from 'aphrodite';
import axios from 'axios';

import {COLUMN_WIDTH} from "../Common/defaults";
import Toolbar from '../Toolbar/Toolbar.js';
import InteractiveNav from '../Nav/InteractiveNav.js';
import {FakeInteractiveReport} from '../Common/sampleReports.js';
import {
  PropagateIndices,
  UpdateSelectedState,
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
} from './reportUtils.js';

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
      navWidth: COLUMN_WIDTH,
      report: null,
      selectedUIDs: [],
      loading: false,
      error: null,
    };
    this.handleNavClick = this.handleNavClick.bind(this);
    this.handlePlayClick = this.handlePlayClick.bind(this);
    this.getReport = this.getReport.bind(this);
  }

  /**
   * Fetch the Testplan report once the component has mounted.
   * @public
   */
  componentDidMount() {
    this.setState({loading: true}, this.getReport);
  }

  /**
   * Fetch the Testplan interactive report and start polling for updates.
   *
   * If running in dev mode we just display a fake report.
   */
  getReport() {
    if (this.props.dev) {
      setTimeout(
        () => this.setState({
          report: FakeInteractiveReport,
          selectedUIDs: this.autoSelect(FakeInteractiveReport),
          loading: false,
        }),
        1500,
      );
    } else {
      axios.get('/api/v1/interactive/report')
      .then(response => {
        if (!this.state.report ||
            this.state.report.hash !== response.data.hash) {
          this.getTests().then(tests => {
            const rawReport = {...response.data, entries: tests};
            const processedReport = PropagateIndices(rawReport);
            this.setState(
              (state, props) => ({
                report: processedReport,
                selectedUIDs: state.selectedUIDs.length > 0 ?
                  state.selectedUIDs : this.autoSelect(processedReport),
                loading: false,
              })
            );
          });
        }
      })
      .catch(error => {
        console.log(error);
        this.setState({error: error, loading: false});
      });

      // We poll for updates to the report every second.
      if (this.props.poll_ms) {
        setTimeout(this.getReport, this.props.poll_ms);
      }
    }
  }

  /**
   * Get the top-level Tests, including their suites and testcases, from the
   * backend.
   */
  getTests() {
    return axios.get(
      "/api/v1/interactive/report/tests"
    ).then(response => {
      return Promise.all(response.data.map(
        newTest => {
          const existingTest = (
            this.state.report && this.state.report.entries.find(
              entry => entry.uid === newTest.uid
            )
          );

          if (!existingTest ||
              existingTest.hash !== newTest.hash) {
            return this.getSuites(newTest, existingTest).then(
              suites => ({...newTest, entries: suites})
            );
          } else {
            return existingTest;
          }
        }
      ));
    });
  }

  /**
   * Get the suites owned by a particular test from the backend.
   */
  getSuites(newTest, existingTest) {
    return axios.get(
      `/api/v1/interactive/report/tests/${newTest.uid}/suites`
    ).then(response => {
      return Promise.all(response.data.map(
        newSuite => {
          const existingSuite = existingTest && existingTest.entries.find(
            entry => entry.uid === newSuite.uid
          );

          if (!existingSuite ||
              existingSuite.hash !== newSuite.hash) {
            return this.getTestCases(newTest, newSuite).then(
              testcases => ({...newSuite, entries: testcases})
            );
          } else {
            return existingSuite;
          }
        }
      ));
    });
  }

  /**
   * Get the testcases owned by a particular test suite from the backend.
   */
  getTestCases(test, suite) {
    return axios.get(
        `/api/v1/interactive/report/tests/${test.uid}/suites/${suite.uid}/` +
        `testcases`
    ).then(response => {
      return response.data;
    });
  }

  /**
   * Auto-select an entry in the report when it is first loaded.
   */
  autoSelect(reportEntry) {
    return [reportEntry.uid];
  }

  /**
   * Request to update an entry in the report via PUT.
   */
  putUpdatedReportEntry(updatedReportEntry) {
    const apiUrl = this.getApiUrl(updatedReportEntry);
    return axios.put(apiUrl, updatedReportEntry);
  }

  /**
   * Get the API URL for requesting to update the state of a report entry.
   */
  getApiUrl(updatedReportEntry) {
    const api_prefix = "/api/v1/interactive";

    switch (updatedReportEntry.parent_uids.length) {
      case 0:
        return api_prefix + "/report";

      case 1: {
        const test_uid = updatedReportEntry.uid;
        return api_prefix + `/report/tests/${test_uid}`;
      }

      case 2: {
        const test_uid = updatedReportEntry.parent_uids[1];
        const suite_uid = updatedReportEntry.uid;

        return api_prefix + `/report/tests/${test_uid}/suites/${suite_uid}`;
      }

      case 3: {
        const test_uid = updatedReportEntry.parent_uids[1];
        const suite_uid = updatedReportEntry.parent_uids[2];
        const testcase_uid = updatedReportEntry.uid;

        return api_prefix + (
          `/report/tests/${test_uid}`
          + `/suites/${suite_uid}`
          + `/testcases/${testcase_uid}`
        );
      }

      default:
        throw new Error(
          "Unexpected number of parent entries: "
          + updatedReportEntry.parent_uids
        );
    }
  }

  /**
   * Update an entry in the report.
   */
  setReportEntry(updatedReportEntry) {
    this.setState((state, props) => ({
      report: this.updateReportEntryRecur(
        updatedReportEntry, state.report,
      ),
    }));
  }

  /**
   * Update a single entry in the report tree recursively. This function
   * returns a new report object, it does not mutate the current report.
   */
  updateReportEntryRecur(updatedReportEntry, currEntry, depth=0) {
    if (depth < updatedReportEntry.parent_uids.length) {
      if (currEntry.uid === updatedReportEntry.parent_uids[depth]) {
        return {
          ...currEntry,
          entries: currEntry.entries.map(
            entry => this.updateReportEntryRecur(
              updatedReportEntry,
              entry,
              depth + 1,
            )
          ),
        };
      } else {
        return currEntry;
      }
    } else if (depth === updatedReportEntry.parent_uids.length) {
      if (updatedReportEntry.uid === currEntry.uid) {
        return updatedReportEntry;
      } else {
        return currEntry;
      }
    } else if (depth > updatedReportEntry.parent_uids.length) {
      throw new Error("Recursed too far down...");
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
  handlePlayClick(e, reportEntry) {
    e.stopPropagation();
    const updatedReportEntry = {
      ...this.shallowReportEntry(reportEntry), status: "running"
    };
    this.putUpdatedReportEntry(updatedReportEntry).then(
      response => this.setReportEntry(PropagateIndices(response.data))
    ).catch(
      error => this.setState({error: error})
    );
  }

  /**
   * Shallow copy of a report entry, by replacing the "entries" attribute
   * with an array of entry UIDs.
   */
  shallowReportEntry(reportEntry) {
    const {entries, ...shallowEntry} = reportEntry;
    shallowEntry.entry_uids = entries.map((entry) => entry.uid);
    return shallowEntry;
  }

  /**
   * Render the InteractiveReport component based on its current state.
   */
  render() {
    const noop = () => undefined;
    const {reportStatus, reportFetchMessage} = GetReportState(this.state);
    const selectedEntries = GetSelectedEntries(
      this.state.selectedUIDs, this.state.report
    );
    const centerPane = GetCenterPane(
      this.state,
      this.props,
      reportFetchMessage,
      null,
      selectedEntries,
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
          selected={selectedEntries}
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

