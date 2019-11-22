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
} from './reportUtils.js';
import {ReportToNavEntry, getNavEntryType} from "../Common/utils";

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
   * Find an entry in our current report from the current selection state.
   */
  findReportEntryFromSelection(selectedEntries, currEntry) {
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
              return this.findReportEntryFromSelection(
                tailSelectedEntries, entry
              );
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
      assertions: this.selectedAssertions(state),
    }));
  }

  /**
   * Return the set of assertions if a testcase is currently selected,
   * otherwise null.
   */
  selectedAssertions(state) {
    const selectedEntry = this.findReportEntryFromSelection(
      state.selected, state.report
    );
    if (getNavEntryType(selectedEntry) === "testcase") {
      return selectedEntry.entries;
    }

    return null;
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
  handlePlayClick(e, navEntry) {
    e.stopPropagation();
    const reportEntry = this.findReportEntryFromNav(navEntry);
    if (!reportEntry) {
      throw new Error("Could not find report entry");
    }

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
   * Find the corresponding entry in the report given a navigation entry.
   * Yes they are subtly different types... (TODO fix this)
   */
  findReportEntryFromNav(navEntry) {
    return this.findReportEntryFromNavRecur(this.state.report, navEntry);
  }

  /**
   * Recursive implementation of finding an entry in the report tree, given
   * its UID and the UIDs of its parent entries.
   */
  findReportEntryFromNavRecur(currEntry, navEntry, depth=0) {
    // Based on our current recursion depth, we either need to check for a
    // match with our current entry and one of the parent UIDs we are
    // searching for, or with the UID of the actual entry we are looking for.
    if (depth < navEntry.parent_uids.length) {
      if (currEntry.uid === navEntry.parent_uids[depth]) {
        // For each child entry, recurse down. If a matching entry is found
        // from any branch, it will be returned back up the stack. Otherwise
        // we return null to indicate that no match was found.
        return currEntry.entries.reduce(
          (foundEntry, childEntry) => {
            if (foundEntry) {
              return foundEntry;
            } else {
              return this.findReportEntryFromNavRecur(
                childEntry, navEntry, depth + 1
              );
            }
          },
          null,
        );
      } else {
        return null;
      }
    } else if (depth === navEntry.parent_uids.length) {
      // We are at the required depth, so no need to recurse any further.
      // Either we have found the entry and return it, or we haven't and
      // return null.
      if (currEntry.uid === navEntry.uid) {
        return currEntry;
      } else {
        return null;
      }
    } else {
      throw new Error("Recursed too far");
    }
  }

  /**
   * Render the InteractiveReport component based on its current state.
   */
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

