/**
 * InteractiveReport: Renders an Interactive report, which is used to control
 * test environments and run tests interactively. Requires the Testplan
 * interactive API backend to be running.
 */
import React from 'react';
import { StyleSheet, css } from 'aphrodite';
import axios from 'axios';
import { Redirect } from "react-router-dom";
import { generatePath } from "react-router";

import Toolbar from '../Toolbar/Toolbar.js';
import { 
  ResetButton,
  ReloadButton,
  SaveButton
} from '../Toolbar/InteractiveButtons';
import InteractiveNav from '../Nav/InteractiveNav.js';
import { INTERACTIVE_COL_WIDTH } from "../Common/defaults";
import { FakeInteractiveReport } from '../Common/sampleReports.js';
import {
  PropagateIndices,  
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
  getSelectedUIDsFromPath,
} from './reportUtils.js';
import {encodeURIComponent2} from '../Common/utils';

import {POLL_MS} from '../Common/defaults.js';

const api_prefix = "/api/v1/interactive";

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
      navWidth: `${INTERACTIVE_COL_WIDTH}em`,
      report: null,      
      loading: false,
      error: null,
      resetting: false,
      reloading: false,
    };
    this.handlePlayClick = this.handlePlayClick.bind(this);
    this.envCtrlCallback = this.envCtrlCallback.bind(this);
    this.getReport = this.getReport.bind(this);
    this.resetReport = this.resetReport.bind(this);
    this.reloadCode = this.reloadCode.bind(this);
    this.handleColumnResizing = this.handleColumnResizing.bind(this);
  }

  /**
   * Fetch the Testplan report once the component has mounted.
   * @public
   */
  componentDidMount() {
    this.setState({ loading: true }, this.getReport);
  }

  setReport(report) {
    const processedReport = PropagateIndices(report);
    this.setState(
      (state, props) => ({
        report: processedReport,
        loading: false,
      })
    );
  }

  /**
   * Fetch the Testplan interactive report and start polling for updates.
   *
   * If running in dev mode we just display a fake report.
   */
  getReport() {
    if (this.props.match.params.uid === '_dev') {
      setTimeout(
        () => this.setReport(FakeInteractiveReport),
        1500,
      );
    } else {
      axios.get('/api/v1/interactive/report')
        .then(response => {
          if (!this.state.report ||
            this.state.report.hash !== response.data.hash) {
            this.getTests().then(tests => {
              const rawReport = { ...response.data, entries: tests };
              this.setReport(rawReport);
            });
          }
        })
        .catch(error => {
          console.log(error);
          this.setState({ error: error, loading: false });
        });

      // We poll for updates to the report every second.
      setTimeout(this.getReport, this.props.poll_intervall || POLL_MS);      
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
              suites => ({ ...newTest, entries: suites })
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
    const encoded_test_uid = encodeURIComponent2(newTest.uid);
    return axios.get(
      `/api/v1/interactive/report/tests/${encoded_test_uid}/suites`
    ).then(response => {
      return Promise.all(response.data.map(
        newSuite => {
          const existingSuite = existingTest && existingTest.entries.find(
            entry => entry.uid === newSuite.uid
          );

          if (!existingSuite ||
            existingSuite.hash !== newSuite.hash) {
            return this.getTestCases(newTest, newSuite, existingSuite).then(
              testcases => ({ ...newSuite, entries: testcases })
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
  getTestCases(test, newSuite, existingSuite) {
    const encoded_test_uid = encodeURIComponent2(test.uid);
    const encoded_suite_uid = encodeURIComponent2(newSuite.uid);
    return axios.get(
      `/api/v1/interactive/report/tests/${encoded_test_uid}/suites/` +
      `${encoded_suite_uid}/testcases`
    ).then(response => {
      return Promise.all(response.data.map((newTestCase) => {
        switch (newTestCase.category) {
          case "testcase":
            return newTestCase;

          case "parametrization":
            const existingParametrization = (
              existingSuite && existingSuite.entries.find(
                entry => entry.uid === newTestCase
              )
            );

            if (
              !existingParametrization ||
              existingParametrization.hash !== newTestCase.hash
            ) {
              return this.getParametrizations(test, newSuite, newTestCase).then(
                parametrizations => ({
                  ...newTestCase, entries: parametrizations
                })
              );
            } else {
              return existingParametrization;
            }

          default:
            throw new Error(
              "Unexpected testcase category: " + newTestCase.category
            );
        }
      }));
    });
  }

  /**
   * Get the parametrizations owned by a particular testcase from the backend.
   */
  getParametrizations(test, suite, testcase) {
    const encoded_test_uid = encodeURIComponent2(test.uid);
    const encoded_suite_uid = encodeURIComponent2(suite.uid);
    const encoded_testcase_uid = encodeURIComponent2(testcase.uid);
    return axios.get(
      `/api/v1/interactive/report/tests/${encoded_test_uid}/suites/` +
      `${encoded_suite_uid}/testcases/${encoded_testcase_uid}/parametrizations`
    ).then(response => response.data);
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
    return axios.put(apiUrl, updatedReportEntry).then(
      response => this.setShallowReportEntry(response.data)
    ).catch(
      error => this.setState({ error: error })
    );
  }

  /**
   * Get the API URL for requesting to update the state of a report entry.
   */
  getApiUrl(updatedReportEntry) {

    switch (updatedReportEntry.parent_uids.length) {
      case 0:
        return api_prefix + "/report";

      case 1: {
        const test_uid = encodeURIComponent2(updatedReportEntry.uid);
        return api_prefix + `/report/tests/${test_uid}`;
      }

      case 2: {
        const test_uid = encodeURIComponent2(updatedReportEntry.parent_uids[1]);
        const suite_uid = encodeURIComponent2(updatedReportEntry.uid);

        return api_prefix + `/report/tests/${test_uid}/suites/${suite_uid}`;
      }

      case 3: {
        const test_uid = encodeURIComponent2(updatedReportEntry.parent_uids[1]);
        const suite_uid = encodeURIComponent2(
          updatedReportEntry.parent_uids[2]
        );
        const testcase_uid = encodeURIComponent2(updatedReportEntry.uid);

        return api_prefix + (
          `/report/tests/${test_uid}`
          + `/suites/${suite_uid}`
          + `/testcases/${testcase_uid}`
        );
      }

      case 4: {
        const test_uid = encodeURIComponent2(updatedReportEntry.parent_uids[1]);
        const suite_uid = encodeURIComponent2(
          updatedReportEntry.parent_uids[2]
        );
        const testcase_uid = encodeURIComponent2(
          updatedReportEntry.parent_uids[3]
        );
        const param_uid = encodeURIComponent2(updatedReportEntry.uid);

        return api_prefix + (
          `/report/tests/${test_uid}`
          + `/suites/${suite_uid}`
          + `/testcases/${testcase_uid}`
          + `/parametrizations/${param_uid}`
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
  setShallowReportEntry(shallowReportEntry) {
    this.setState((state, props) => ({
      report: this.updateReportEntryRecur(
        shallowReportEntry, state.report,
      ),
    }));
  }

  /**
   * Update a single entry in the report tree recursively. This function
   * returns a new report object, it does not mutate the current report.
   */
  updateReportEntryRecur(shallowReportEntry, currEntry, depth = 0) {
    if (depth < shallowReportEntry.parent_uids.length) {
      if (currEntry.uid === shallowReportEntry.parent_uids[depth]) {
        return {
          ...currEntry,
          hash: null,  // clear the hash on the path down to the change, as we
                       // do not know what it would be safe bet to set null
          entries: currEntry.entries.map(
            entry => this.updateReportEntryRecur(
              shallowReportEntry,
              entry,
              depth + 1,
            )
          ),
        };
      } else {
        return currEntry;
      }
    } else if (depth === shallowReportEntry.parent_uids.length) {
      if (shallowReportEntry.uid === currEntry.uid) {
        return this.unshallowReportEntry(shallowReportEntry, currEntry);
      } else {
        return currEntry;
      }
    } else if (depth > shallowReportEntry.parent_uids.length) {
      throw new Error("Recursed too far down...");
    }
  }

  /**
   * Convert a shallow report entry to an "unshallow" one with embedded
   * entries, by stealing the entries (and some other metadata) from
   * the current entry.
   */
  unshallowReportEntry(shallowReportEntry, currReportEntry) {
    const newEntry = {
      ...shallowReportEntry,
      entries: currReportEntry.entries,
      tags: currReportEntry.tags,
      tags_index: currReportEntry.tags_index,
      name_type_index: currReportEntry.name_type_index,
      uids: currReportEntry.uids,
      counter: currReportEntry.counter,
    };
    delete newEntry.entry_uids;

    return newEntry;
  }

  /**
   * Handle resizing event and update NavList & Center Pane.
   */
  handleColumnResizing(navWidth) {
    this.setState({navWidth: navWidth});
  }

  /* Handle the play button being clicked on a Nav entry. */
  handlePlayClick(e, reportEntry) {
    e.preventDefault();
    e.stopPropagation();
    const updatedReportEntry = {
      ...this.shallowReportEntry(reportEntry), runtime_status: "running"
    };
    this.putUpdatedReportEntry(updatedReportEntry);
  }

  /**
   * Handle an environment toggle button being clicked on a Nav entry.
   *
   * @param {object} e - Click event
   * @param {ReportNode} reportEntry - entry in the report whose environment
   *                                   has been toggled.
   * @param {string} action - What action to take on the environment, expected
   *                          to be one of "start" or "stop".
   */
  envCtrlCallback(e, reportEntry, action) {
    e.preventDefault();
    e.stopPropagation();
    const updatedReportEntry = {
      ...this.shallowReportEntry(reportEntry),
      env_status: this.actionToEnvStatus(action),
    };
    this.putUpdatedReportEntry(updatedReportEntry);
  }

  /**
   * Convert an environment action into a requested environment status.
   *
   * @param {string} action - environment action, one of "start" or "stop".
   * @return {string} env_status value to use in API request.
   */
  actionToEnvStatus(action) {
    switch (action) {
      case "start":
        return "STARTING";

      case "stop":
        return "STOPPING";

      default:
        throw new Error("Invalid action: " + action);
    }
  }

  /**
   * Shallow copy of a report entry, by replacing the "entries" attribute
   * with an array of entry UIDs.
   */
  shallowReportEntry(reportEntry) {
    const { entries, ...shallowEntry } = reportEntry;
    shallowEntry.entry_uids = entries.map((entry) => entry.uid);
    return shallowEntry;
  }

  /**
   * Reset the report state, by updating all testcases to have no entries.
   */
  resetReport() {
    let needReset = false;
    this.setState((state) => {
      if (state.resetting) {
        return null;
      }

      needReset = true;
      return { resetting: true };
    },
      () => {
        if (needReset) {
          this.resetEnvironment().then(() => {
            this.resetTestcasesRecur(this.state.report).then(
              () => this.setState({ resetting: false })
            );
          }).catch(error => {
            console.log(error);
            this.setState({ resetting: false, error: error });
          });
        }
      }
    );
  }

  reloadCode() {
    let currentTime = new Date();
    this.setState({reloading: true});
    return axios.get(
      `${api_prefix}/reload`
    ).then(response => {
      let duration = new Date() - currentTime;
      if (duration < 1000) {
        setTimeout(()=> {
          this.setState({reloading: false});
        }, 1000);
      } else {
        this.setState({reloading: false});
      }
      return;
    });
  }

  /**
   * Recursievly dig down into the report tree and reset the state of any
   * testcase entries. Other entries derive their state from the testcases
   * so their state updates will be provided to us by the backend.
   */
  resetTestcasesRecur(reportEntry) {
    if (reportEntry.category === "testcase") {
      if (reportEntry.entries.length === 0) {
        return null;
      } else {
        const updatedReportEntry = {
          ...reportEntry,
          entries: [],
        };
        return this.putUpdatedReportEntry(updatedReportEntry);
      }
    } else if (reportEntry.entries) {
      return Promise.all(reportEntry.entries.map(
        childEntry => this.resetTestcasesRecur(childEntry)
      ));
    }
  }

  /**
   * Reset the environment state by stopping all started environments.
   */
  resetEnvironment() {
    return Promise.all(this.state.report.entries.map(reportEntry => {
      const updatedReportEntry = {
        ...reportEntry,
        env_status: reportEntry.env_status === "STARTED" ?
          "STOPPING" : reportEntry.env_status,
      };
      return this.putUpdatedReportEntry(updatedReportEntry);
    }));
  }

  /**
   * Render the InteractiveReport component based on its current state.
   */
  render() {

    if ( this.props.match.params.uid === undefined && this.state.report) {
      return <Redirect to={generatePath(this.props.match.path,
        {uid: this.state.report.uid, selection:undefined})}/>;
    }

    const noop = () => undefined;
    const { reportStatus, reportFetchMessage } = GetReportState(this.state);
    const selectedEntries = GetSelectedEntries(
      getSelectedUIDsFromPath(this.props.match.params), this.state.report
    );
    const centerPane = GetCenterPane(
      this.state,
      reportFetchMessage,
      null,
      selectedEntries,
    );

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          filterBoxWidth={this.state.navWidth}
          status={reportStatus}
          handleNavFilter={null}
          updateFilterFunc={noop}
          updateEmptyDisplayFunc={noop}
          updateTagsDisplayFunc={noop}
          extraButtons={[
            <ReloadButton
              reloading={this.state.reloading}
              reloadCbk={this.reloadCode}
            />,
            <SaveButton key="save-button"/>,
            <ResetButton
            key="time-button"
            resetStateCbk={this.resetReport}
            resetting={false}
          />
          ]}
        />
        <InteractiveNav
          navListWidth={this.state.navWidth}
          report={this.state.report}
          selected={selectedEntries}
          filter={null}
          displayEmpty={true}
          displayTags={false}
          displayTime={false}          
          handlePlayClick={this.handlePlayClick}
          envCtrlCallback={this.envCtrlCallback}
          handleColumnResizing={this.handleColumnResizing}
          url={this.props.match.path}
        />
        {centerPane}
      </div>
    );
  }
}

const styles = StyleSheet.create({ interactiveReport: {} });

export default InteractiveReport;

