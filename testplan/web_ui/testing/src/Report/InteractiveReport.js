/**
 * InteractiveReport: Renders an Interactive report, which is used to control
 * test environments and run tests interactively. Requires the Testplan
 * interactive API backend to be running.
 */
// React needs to be in scope for JSX
import React from "react";
import { StyleSheet, css } from "aphrodite";
import axios from "axios";
import { Redirect } from "react-router-dom";
import { generatePath } from "react-router";
import base64url from "base64url";

import BaseReport from "./BaseReport";
import Toolbar from "../Toolbar/Toolbar.js";
import {
  ReloadButton,
  ResetButton,
  AbortButton,
  SaveButton,
} from "../Toolbar/InteractiveButtons";
import NavBreadcrumbs from "../Nav/NavBreadcrumbs";
import Nav from "../Nav/Nav.js";
import { INTERACTIVE_COL_WIDTH } from "../Common/defaults";
import { FakeInteractiveReport } from "../Common/sampleReports.js";
import {
  PropagateIndices,
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
  filterReport,
  getSelectedUIDsFromPath,
} from "./reportUtils.js";
import { GetNavBreadcrumbs } from "../Nav/navUtils";

import { encodeURIComponent2, parseToJson } from "../Common/utils";

import { POLL_MS } from "../Common/defaults.js";
import { AssertionContext, defaultAssertionStatus } from "../Common/context";
import { ErrorBoundary } from "../Common/ErrorBoundary";
import { displayTimeInfoPreference } from "../UserSettings/UserSettings";
import { useAtomValue } from "jotai";

const api_prefix = "/api/v1/interactive";

/**
 * Interactive report viewer. As opposed to a batch report, an interactive
 * report starts off with no test results and fills up with results as
 * the tests are run interactively. Tests can be run by clicking buttons in
 * the UI.
 */
const InteractiveReport = (props) => {
  const displayTimeInfo = useAtomValue(displayTimeInfoPreference);
  return (
    <InteractiveReportComponent {...props} displayTimeInfo={displayTimeInfo} />
  );
};
class InteractiveReportComponent extends BaseReport {
  constructor(props) {
    super(props);
    this.setReport = this.setReport.bind(this);
    this.getReport = this.getReport.bind(this);
    this.resetAssertionStatus = this.resetAssertionStatus.bind(this);
    this.resetReport = this.resetReport.bind(this);
    this.abortTestplan = this.abortTestplan.bind(this);
    this.reloadCode = this.reloadCode.bind(this);
    this.envCtrlCallback = this.envCtrlCallback.bind(this);
    this.handleClick = this.handleClick.bind(this);

    this.state = {
      ...this.state,
      navWidth: `${INTERACTIVE_COL_WIDTH}em`,
      resetting: false,
      reloading: false,
      aborting: false,
      assertionStatus: defaultAssertionStatus,
    };
  }

  setReport(report) {
    const processedReport = PropagateIndices(report);
    const filteredReport = filterReport(
      processedReport,
      this.state.filteredReport.filter
    );
    this.setState((state, props) => ({
      report: processedReport,
      filteredReport,
      loading: false,
    }));
  }

  /**
   * reset the expand status of assertions
   */
  resetAssertionStatus() {
    this.setState((prev) => {
      const assertionStatus = prev.assertionStatus;
      assertionStatus.assertions = {};
      return { ...prev, assertionStatus };
    });
  }

  /**
   * Fetch the Testplan interactive report and start polling for updates.
   *
   * If running in dev mode we just display a fake report.
   */
  getReport() {
    if (this.state.aborting) {
      this.setError({ message: "Server is aborting ..." });
      return;
    }
    if (this.props.match.params.uid === "_dev") {
      setTimeout(() => this.setReport(FakeInteractiveReport), 1500);
    } else {
      axios
        .get("/api/v1/interactive/report", { transformResponse: parseToJson })
        .then((response) => {
          if (
            response.data.runtime_status === "ready" ||
            response.data.runtime_status === "finished" ||
            response.data.runtime_status === "not_run"
          ) {
            this.setState({ resetting: false });
          }
          if (
            !this.state.report ||
            this.state.report.hash !== response.data.hash
          ) {
            this.getTests().then((tests) => {
              const rawReport = { ...response.data, entries: tests };
              this.setReport(rawReport);
            });
          }
        })
        .catch(this.setError)
        .finally(() => {
          // We poll for updates to the report every second.
          setTimeout(this.getReport, this.props.poll_intervall || POLL_MS);
        });
    }
  }

  /**
   * Get the top-level Tests, including their suites and testcases, from the
   * backend.
   */
  getTests() {
    return axios
      .get("/api/v1/interactive/report/tests", {
        transformResponse: parseToJson,
      })
      .then((response) => {
        return Promise.all(
          response.data.map((newTest) => {
            const existingTest =
              this.state.report &&
              this.state.report.entries.find(
                (entry) => entry.uid === newTest.uid
              );

            if (!existingTest || existingTest.hash !== newTest.hash) {
              return this.getSuites(newTest, existingTest).then((suites) => ({
                ...newTest,
                entries: suites,
              }));
            } else {
              return existingTest;
            }
          })
        );
      });
  }

  /**
   * Get the suites owned by a particular test from the backend.
   */
  getSuites(newTest, existingTest) {
    const encoded_test_uid = encodeURIComponent2(newTest.uid);
    return axios
      .get(`/api/v1/interactive/report/tests/${encoded_test_uid}/suites`, {
        transformResponse: parseToJson,
      })
      .then((response) => {
        return Promise.all(
          response.data.map((newSuite) => {
            const existingSuite =
              existingTest &&
              existingTest.entries.find((entry) => entry.uid === newSuite.uid);

            if (!existingSuite || existingSuite.hash !== newSuite.hash) {
              return this.getTestCases(newTest, newSuite, existingSuite).then(
                (testcases) => ({ ...newSuite, entries: testcases })
              );
            } else {
              return existingSuite;
            }
          })
        );
      });
  }

  /**
   * Get the testcases owned by a particular test suite from the backend.
   */
  getTestCases(test, newSuite, existingSuite) {
    const encoded_test_uid = encodeURIComponent2(test.uid);
    const encoded_suite_uid = encodeURIComponent2(newSuite.uid);
    return axios
      .get(
        `/api/v1/interactive/report/tests/${encoded_test_uid}/suites/` +
          `${encoded_suite_uid}/testcases`,
        { transformResponse: parseToJson }
      )
      .then((response) => {
        return Promise.all(
          response.data.map((newTestCase) => {
            switch (newTestCase.category) {
              case "testcase":
                return newTestCase;

              case "parametrization":
                const existingParametrization =
                  existingSuite &&
                  existingSuite.entries.find(
                    (entry) => entry.uid === newTestCase
                  );

                if (
                  !existingParametrization ||
                  existingParametrization.hash !== newTestCase.hash
                ) {
                  return this.getParametrizations(
                    test,
                    newSuite,
                    newTestCase
                  ).then((parametrizations) => ({
                    ...newTestCase,
                    entries: parametrizations,
                  }));
                } else {
                  return existingParametrization;
                }

              default:
                throw new Error(
                  "Unexpected testcase category: " + newTestCase.category
                );
            }
          })
        );
      });
  }

  /**
   * Get the parametrizations owned by a particular testcase from the backend.
   */
  getParametrizations(test, suite, testcase) {
    const encoded_test_uid = encodeURIComponent2(test.uid);
    const encoded_suite_uid = encodeURIComponent2(suite.uid);
    const encoded_testcase_uid = encodeURIComponent2(testcase.uid);
    return axios
      .get(
        `/api/v1/interactive/report/tests/${encoded_test_uid}/suites/` +
          `${encoded_suite_uid}/testcases/${encoded_testcase_uid}/parametrizations`,
        { transformResponse: parseToJson }
      )
      .then((response) => response.data);
  }

  /**
   * Request to update an entry in the report via PUT.
   */
  putUpdatedReportEntry(updatedReportEntry) {
    const apiUrl = this.getApiUrl(updatedReportEntry);
    return axios
      .put(apiUrl, updatedReportEntry)
      .then((response) => {
        if (response.data.errmsg) {
          console.error(response.data);
          alert(response.data.errmsg);
        } else {
          // Do not update report hash here.
          response.data.hash = updatedReportEntry.hash;
          this.setShallowReportEntry(response.data);
        }
      })
      .catch((error) => this.setState({ error: error }));
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

        return (
          api_prefix +
          (`/report/tests/${test_uid}` +
            `/suites/${suite_uid}` +
            `/testcases/${testcase_uid}`)
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

        return (
          api_prefix +
          (`/report/tests/${test_uid}` +
            `/suites/${suite_uid}` +
            `/testcases/${testcase_uid}` +
            `/parametrizations/${param_uid}`)
        );
      }

      default:
        throw new Error(
          "Unexpected number of parent entries: " +
            updatedReportEntry.parent_uids
        );
    }
  }

  /**
   * Update an entry in the report.
   */
  setShallowReportEntry(shallowReportEntry) {
    this.setState((state, props) => ({
      report: this.updateReportEntryRecur(shallowReportEntry, state.report),
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
          hash: null, // clear the hash on the path down to the change, as we
          // do not know what it would be safe bet to set null
          entries: currEntry.entries.map((entry) =>
            this.updateReportEntryRecur(shallowReportEntry, entry, depth + 1)
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
   * Handle the play/reset buttons being clicked on a Nav entry.
   */
  handleClick(e, reportEntry, action) {
    e.preventDefault();
    e.stopPropagation();
    const updatedReportEntry = {
      ...this.shallowReportEntry(reportEntry),
      runtime_status: action,
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
   * Prunes the report entry recursively so that only name, category, and
   * entries attributes are preserved.
   */
  pruneReportEntry(reportEntry) {
    const { name, category, entries } = reportEntry;
    const pruneEntry = {
      name: name,
      category: category,
    };

    if (entries.length !== 0 && category !== "testcase") {
      pruneEntry.entries = entries.map((entry) => this.pruneReportEntry(entry));
    }

    return pruneEntry;
  }

  /**
   * Shallow copy of a report entry, by replacing the "entries" attribute
   * with an array of entry UIDs if not filter is present.
   * In case there is a non-empty filter text, the entries attribute is pruned.
   */
  shallowReportEntry(reportEntry) {
    const { entries, ...shallowEntry } = reportEntry;
    shallowEntry.entry_uids = entries.map((entry) => entry.uid);

    // the filter text is either "null" or an empty string, use truthy-falsy
    if (this.state.filteredReport.filter.text) {
      shallowEntry.entries = entries.map((entry) =>
        this.pruneReportEntry(entry)
      );
    }

    return shallowEntry;
  }

  /**
   * Reset the report state to "resetting" and request the change to server.
   */
  resetReport() {
    if (this.state.resetting || this.state.reloading || this.state.aborting) {
      return;
    } else {
      const updatedReportEntry = {
        ...this.shallowReportEntry(this.state.report),
        runtime_status: "resetting",
      };
      this.putUpdatedReportEntry(updatedReportEntry);
      this.setState({ resetting: true });
    }
  }

  /**
   * Send request of reloading report to server.
   */
  reloadCode() {
    if (this.state.resetting || this.state.reloading || this.state.aborting) {
      return;
    }
    let currentTime = new Date();
    this.setState({ reloading: true });
    this.resetAssertionStatus();
    return axios
      .get(`${api_prefix}/reload`)
      .then((response) => {
        if (response.data.errmsg) {
          alert(response.data.errmsg);
          console.error(response.data);
        }
        let duration = new Date() - currentTime;
        if (duration < 1000) {
          setTimeout(() => {
            this.setState({ reloading: false });
          }, 1000);
        } else {
          this.setState({ reloading: false });
        }
        return;
      })
      .catch((error) => {
        alert("Cannot reload when there is test not finished.");
        setTimeout(() => {
          this.setState({ reloading: false });
        }, 1000);
      });
  }

  /**
   * Send request of aborting Testing to server.
   */
  abortTestplan() {
    if (this.state.aborting) {
      return;
    }
    if (!window.confirm("Abort Testplan ?")) {
      return;
    }
    this.setState({ aborting: true });
    return axios
      .get(`${api_prefix}/abort`)
      .then((response) => {
        if (response.data.errmsg) {
          alert(response.data.errmsg);
          console.error(response.data);
          this.setState({ aborting: false });
        } else {
          alert("Testplan aborted, please close this windows.");
          this.setError({ message: "Server aborted !!!" });
          window.close();
        }
      })
      .catch((error) => {
        alert("Unknown error, please close this windows.");
        this.setError({ message: "Cannot connect to server !!!" });
        window.close();
      });
  }

  /**
   * Recursively dig down into the report tree and reset the state of any
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
      return Promise.all(
        reportEntry.entries.map((childEntry) =>
          this.resetTestcasesRecur(childEntry)
        )
      );
    }
  }

  /**
   * Reset the environment state by stopping all started environments.
   */
  resetEnvironment() {
    return Promise.all(
      this.state.report.entries.map((reportEntry) => {
        const updatedReportEntry = {
          ...reportEntry,
          env_status:
            reportEntry.env_status === "STARTED"
              ? "STOPPING"
              : reportEntry.env_status,
        };
        return this.putUpdatedReportEntry(updatedReportEntry);
      })
    );
  }

  /**
   * Render the InteractiveReport component based on its current state.
   */
  render() {
    if (this.props.match.params.uid === undefined && this.state.report) {
      return (
        <Redirect
          to={generatePath(this.props.match.path, {
            uid: base64url(this.state.report.uid),
            selection: undefined,
          })}
        />
      );
    }

    const noop = () => undefined;
    const { reportStatus, reportFetchMessage } = GetReportState(this.state);
    const selectedEntries = GetSelectedEntries(
      getSelectedUIDsFromPath(this.props.match.params, base64url.decode),
      this.state.filteredReport.report
    );
    const centerPane = GetCenterPane(
      this.state,
      reportFetchMessage,
      null,
      selectedEntries,
      this.props.displayTimeInfo
    );

    return (
      <div className={css(styles.interactiveReport)}>
        <Toolbar
          filterBoxWidth={this.state.navWidth}
          filterText={this.state.filteredReport.filter.text}
          status={reportStatus}
          expandStatus={this.state.assertionStatus.globalExpand.status}
          updateExpandStatusFunc={this.updateGlobalExpand}
          handleNavFilter={this.handleNavFilter}
          updateFilterFunc={noop}
          updateEmptyDisplayFunc={noop}
          updateTagsDisplayFunc={noop}
          extraButtons={[
            <ReloadButton
              key="reload-button"
              reloading={this.state.reloading}
              reloadCbk={this.reloadCode}
            />,
            <ResetButton
              key="reset-button"
              resetting={this.state.resetting}
              resetStateCbk={this.resetReport}
            />,
            <AbortButton
              key="abort-button"
              aborting={this.state.aborting}
              abortCbk={this.abortTestplan}
            />,
            <SaveButton key="save-button" />,
          ]}
        />
        <NavBreadcrumbs
          entries={GetNavBreadcrumbs(selectedEntries)}
          url={this.props.match.path}
          uidEncoder={base64url}
        />
        <div
          style={{
            display: "flex",
            flex: "1",
            overflowY: "auto",
          }}
        >
          <Nav
            interactive={true}
            navListWidth={this.state.navWidth}
            report={this.state.filteredReport.report}
            selected={selectedEntries}
            filter={null}
            displayTags={false}
            displayTime={false}
            // envCtrlCallback and handleClick are passed down to InteractiveNav
            handleClick={this.handleClick}
            envCtrlCallback={this.envCtrlCallback}
            handleColumnResizing={this.handleColumnResizing}
            url={this.props.match.path}
          />
          <AssertionContext.Provider value={this.state.assertionStatus}>
            <ErrorBoundary>{centerPane}</ErrorBoundary>
          </AssertionContext.Provider>
        </div>
      </div>
    );
  }
}

const styles = StyleSheet.create({
  interactiveReport: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
});

export default InteractiveReport;
export { InteractiveReportComponent };
