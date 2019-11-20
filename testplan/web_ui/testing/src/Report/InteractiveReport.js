/**
 * InteractiveReport: Renders an Interactive report, which is used to control
 * test environments and run tests interactively. Requires the Testplan
 * interactive API backend to be running.
 */
import React from 'react';
import {StyleSheet, css} from 'aphrodite';
import axios from 'axios';

import {COLUMN_WIDTH} from "../Common/defaults";
import {getNavEntryType} from "../Common/utils";
import Toolbar from '../Toolbar/Toolbar.js';
import InteractiveNav from '../Nav/InteractiveNav.js';
import {FakeInteractiveReport} from '../Common/sampleReports.js';
import {
  PropagateIndices,
  UpdateSelectedState,
  GetReportState,
  GetCenterPane,
} from './reportUtils.js';
import {ReportToNavEntry} from "../Common/utils";

// Interval to poll for report updates over. We may want to reduce this to make
// the UI update more quickly.
//
// NOTE: currently we poll for updates using HTTP for simplicity but in future
// it might be better to use websockets or SSEs to allow the backend to notify
// us when updates are available.
const POLL_MS = 1000;

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
          selected: this.autoSelect(FakeInteractiveReport),
          loading: false,
        }),
        1500,
      );
    } else {
      axios.get('/api/v1/interactive/report')
      .then(response => {
        this.getTests().then(tests => {
          const rawReport = {...response.data, entries: tests};
          const processedReport = PropagateIndices(rawReport);
          this.setState(
            (state, props) => ({
              report: processedReport,
              selected: state.selected.length > 0 ?
                state.selected : this.autoSelect(processedReport),
              loading: false,
            })
          );
        });
      })
      .catch(error => {
        console.log(error);
        this.setState({error: error, loading: false});
      });

      // We poll for updates to the report every second. Currently we
      // completely refresh the whole report, which is clearly
      // inefficient for largish reports. In future we should add
      // a mechanism to tell when we can partially update the report,
      // e.g. by adding update timestamps to report entries or by
      // subscribing to notifications from the backend when specific
      // entries are updated.
      setTimeout(this.getReport, POLL_MS);
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
        test => this.getSuites(test)
          .then(suites => ({...test, entries: suites}))
      ));
    });
  }


  /**
   * Get the suites owned by a particular test from the backend.
   */
  getSuites(test) {
    return axios.get(
      `/api/v1/interactive/report/tests/${test.uid}/suites`
    ).then(response => {
      return Promise.all(
        response.data.map((suite) => this.getTestCases(test, suite)
          .then(testcases => ({...suite, entries: testcases}))
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
    return [ReportToNavEntry(reportEntry)];
  }

  /**
   * Find a report entry in our current report state given the selected
   * navigation entries.
   */
  findReportEntry(selectedEntries, currEntry) {
    const [headSelectedEntry, ...tailSelectedEntries] = selectedEntries;
    const match = (currEntry.uid === headSelectedEntry.uid);

    // Check if the UID matches.
    if (match) {
      // Two cases to distinguish between:
      //
      // - There are more selected entries to search down for: we recurse down.
      // - There are no more selected entries: we have found the matching
      //   report entry, so return it.
      if (tailSelectedEntries.length === 0) {
        return currEntry;
      } else {
        return currEntry.entries.reduce(
          (accumulator, entry) => {
            if (accumulator) {
              return accumulator;
            } else {
              return this.findReportEntry(tailSelectedEntries, entry);
            }
          },
          null,
        );
      }
    } else {
      // Return null to indicate no match.
      return null;
    }
  }

  /**
   * Request to update an entry in the report via PUT.
   */
  putUpdatedReportEntry(updatedReportEntry, selectedEntries) {
    const apiUrl = this.getApiUrl(updatedReportEntry, selectedEntries);
    return axios.put(apiUrl, updatedReportEntry);
  }

  /**
   * Get the API URL for requesting to update the state of a report entry.
   */
  getApiUrl(updatedReportEntry, selectedEntries) {
    const api_prefix = "/api/v1/interactive";

    switch (selectedEntries.length) {
      case 1:
        return api_prefix + "/report";

      case 2: {
        const test_uid = selectedEntries[1].uid;
        return api_prefix + `/report/tests/${test_uid}`;
      }

      case 3: {
        const test_uid = selectedEntries[1].uid;
        const suite_uid = selectedEntries[2].uid;
        return api_prefix + `/report/tests/${test_uid}/suites/${suite_uid}`;
      }

      case 4: {
        const test_uid = selectedEntries[1].uid;
        const suite_uid = selectedEntries[2].uid;
        const testcase_uid = selectedEntries[3].uid;
        return api_prefix + (
          `/report/tests/${test_uid}`
          + `/suites/${suite_uid}`
          + `/testcases/${testcase_uid}`
        );
      }

      default:
        throw new Error(
          "Unexpected number of selected entries: " + selectedEntries
        );
    }
  }

  /**
   * Update an entry in the report.
   */
  setReportEntry(updatedReportEntry, selectedEntries) {
    this.setState((state, props) => ({
      report: this.updateReportEntryRecur(
        updatedReportEntry, selectedEntries, state.report
      ),
      assertions: this.selectedAssertions(state),
    }));
  }

  /**
   * Return the set of assertions if a testcase is currently selected,
   * otherwise null.
   */
  selectedAssertions(state) {
    const selectedEntry = this.findReportEntry(state.selected, state.report);
    if (getNavEntryType(selectedEntry) === "testcase") {
      return selectedEntry.entries;
    }

    return null;
  }

  /**
   * Update a single entry in the report tree recursively. This function
   * returns a new report object, it does not mutate the current report.
   */
  updateReportEntryRecur(updatedReportEntry, selectedEntries, currEntry) {
    const [headSelectedEntry, ...tailSelectedEntries] = selectedEntries;
    const match = (currEntry.uid === headSelectedEntry.uid);

    // Check if the UID matches.
    if (match) {
      // Two cases to distinguish between:
      //
      // - There are more selected entries to search down for: we recurse down.
      // - There are no more selected entries: we have found the matching
      //   report entry, so return it.
      if (tailSelectedEntries.length === 0) {
        return updatedReportEntry;
      } else {
        return {
          ...currEntry,
          entries: currEntry.entries.map(
            entry => this.updateReportEntryRecur(
              updatedReportEntry,
              tailSelectedEntries,
              entry,
            )
          ),
        };
      }
    } else {
      // Return entry unchanged.
      return currEntry;
    }
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
  handlePlayClick(e, entry) {
    e.stopPropagation();

    // To be able to update the correct entry in the report tree efficiently,
    // we need to know the hierarchy of parent entries. Currently we do this
    // by inspecting the array of selected entry UIDs. In future it would
    // be better if the UIDs of parent entries could be stored on each
    // report entry so that we don't need to do it this way.
    const currSelected = this.state.selected[this.state.selected.length - 1];
    if (currSelected.type === "testcase") {
      // When testcases are selected, there is an additional complication:
      // the testcase that is being run may not be the same testcase that is
      // currently selected. In that case we swap out the UIDs in the selected
      // array before passing it down (this does not affect the actual
      // selected entries in this component's state).
      if (currSelected.uid === entry.uid) {
        this.runEntry(this.state.selected);
      } else {
        const runEntryHierarchy = this.state.selected.slice(0, -1).concat(
          [ReportToNavEntry(entry)]
        );
        this.runEntry(runEntryHierarchy);
      }
    } else {
      const runEntryHierarchy = this.state.selected.concat(
        [ReportToNavEntry(entry)]
      );
      this.runEntry(runEntryHierarchy);
    }
  }

  /**
   * Trigger the run of either a single testcase or a group of testcases
   * (suite, MultiTest or Testplan) represented by an entry in the report.
   */
  runEntry(selectedEntries) {
    const reportEntry = this.findReportEntry(
      selectedEntries, this.state.report
    );
    if (!reportEntry) {
      console.log(selectedEntries);
      throw new Error("Could not find entry to run");
    }

    const updatedReportEntry = {...reportEntry, status: "running"};

    // TODO handle request error by resyncing report state.
    this.putUpdatedReportEntry(updatedReportEntry, selectedEntries)
      .then(response => this.setReportEntry(
        PropagateIndices(response.data), selectedEntries
      ))
      .catch(error => this.setState({error: error}));
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

