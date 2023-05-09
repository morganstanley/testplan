// React needs to be in scope for JSX
import React from "react";
import { StyleSheet, css } from "aphrodite";
import axios from "axios";
import PropTypes from "prop-types";
import _ from "lodash";

import { parseToJson } from "../Common/utils";
import BaseReport from "./BaseReport";
import Toolbar from "../Toolbar/Toolbar";
import NavBreadcrumbs from "../Nav/NavBreadcrumbs";
import Nav from "../Nav/Nav";
import {
  PropagateIndices,
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
  MergeSplittedReport,
  findFirstFailure,
  filterReport,
  getSelectedUIDsFromPath,
} from "./reportUtils";
import { generateSelectionPath } from "./path";

import { COLUMN_WIDTH, defaultFixSpec } from "../Common/defaults";
import { AssertionContext } from "../Common/context";
import {
  fakeReportAssertions,
  fakeReportAssertionsError,
} from "../Common/fakeReport";

/**
 * BatchReport component:
 *   * fetch Testplan report.
 *   * display messages when loading report or error in report.
 *   * render toolbar, nav & assertion components.
 */
class BatchReport extends BaseReport {
  constructor(props) {
    super(props);
    this.setReport = this.setReport.bind(this);
    this.getReport = this.getReport.bind(this);
    this.updateDisplayEmpty = this.updateDisplayEmpty.bind(this);
    this.updateTagsDisplay = this.updateTagsDisplay.bind(this);
    this.updateFilter = this.updateFilter.bind(this);

    this.state = {
      ...this.state,
      navWidth: `${COLUMN_WIDTH}em`,
      testcaseUid: null,
      filter: null,
      displayTags: false,
      displayEmpty: true,
    };
  }

  setReport(report) {
    const processedReport = PropagateIndices(report);
    const filteredReport = filterReport(
      processedReport,
      this.state.filteredReport.filter
    );
    const firstFailedUID =
      filteredReport.report.status === "failed" ||
      filteredReport.report.status === "error"
        ? findFirstFailure(filteredReport.report)
        : [filteredReport.report.uid];

    const redirectPath = this.props.match.params.selection
      ? null
      : generateSelectionPath(this.props.match.path, firstFailedUID);

    if (redirectPath) {
      this.props.history.replace(redirectPath);
    }

    this.setState({
      report: processedReport,
      filteredReport,
      loading: false,
    });
  }

  /**
   * Fetch the Testplan report.
   *   * Get the UID from the URL.
   *   * Handle UID errors.
   *   * Make a GET request for the Testplan report.
   *   * Handle error response.
   * @public
   */
  getReport() {
    // Inspect the UID to determine the report to render. As a special case,
    // we will display a fake report for development purposes.
    const uid = this.props.match.params.uid;
    axios
      .get("/api/v1/metadata/fix-spec/tags")
      .then((metadataRes) => {
        defaultFixSpec.tags = metadataRes.data || {};
      })
      .catch((error) => {
        console.log(error);
      });
    switch (uid) {
      case "_dev":
        setTimeout(
          () => this.setReport(this.updateReportUID(fakeReportAssertions, uid)),
          1500
        );
        break;
      case "_dev_error":
        setTimeout(
          () =>
            this.setReport(
              this.updateReportUID(fakeReportAssertionsError, uid)
            ),
          1500
        );
        break;
      default:
        axios
          .get(`/api/v1/reports/${uid}`)
          .then((response) => {
            const rawReport = response.data;
            if (rawReport.version === 2) {
              const assertionsReq = axios.get(
                `/api/v1/reports/${uid}/attachments/` +
                  `${rawReport.assertions_file}`,
                { transformResponse: parseToJson }
              );
              const structureReq = axios.get(
                `/api/v1/reports/${uid}/attachments/` +
                  `${rawReport.structure_file}`,
                { transformResponse: parseToJson }
              );
              axios
                .all([assertionsReq, structureReq])
                .then(
                  axios.spread((assertionsRes, structureRes) => {
                    if (!assertionsRes.data) {
                      console.error(assertionsRes);
                      alert(
                        "Failed to parse assertion datails!\n" +
                          "Please report this issue to the Testplan team."
                      );
                    }
                    const mergedReport = MergeSplittedReport(
                      rawReport,
                      assertionsRes.data,
                      structureRes.data
                    );
                    this.setReport(this.updateReportUID(mergedReport, uid));
                  })
                )
                .catch(this.setError);
            } else {
              this.setReport(this.updateReportUID(rawReport, uid));
            }
          })
          .catch(this.setError);
        break;
    }
  }

  updateReportUID(report, uid) {
    return { ...report, uid };
  }

  /**
   * Update the global filter state of the entry.
   *
   * @param {string} filter - null, all, pass or fail.
   * @public
   */
  updateFilter(filter) {
    this.setState({ filter: filter });
  }

  /**
   * Update tag display of each navigation entry.
   *
   * @param {boolean} displayTags.
   * @public
   */
  updateTagsDisplay(displayTags) {
    this.setState({ displayTags: displayTags });
  }

  /**
   * Update navigation pane to show/hide entries of empty testcases.
   *
   * @param {boolean} displayEmpty.
   * @public
   */
  updateDisplayEmpty(displayEmpty) {
    this.setState({ displayEmpty: displayEmpty });
  }

  getSelectedUIDsFromPath() {
    const { uid, selection } = this.props.match.params;
    return [uid, ...(selection ? selection.split("/") : [])];
  }

  selectionMatchPath(entries_selection) {
    let [uid, ...selection] =
      entries_selection[entries_selection.length - 1].uids;

    selection = selection.length ? selection.join("/") : undefined;

    return (
      uid === this.props.match.params.uid &&
      selection === this.props.match.params.selection
    );
  }

  render() {
    const { reportStatus, reportFetchMessage } = GetReportState(this.state);

    if (this.state.report && this.state.report.name) {
      window.document.title = this.state.report.name;
    }

    const selectedEntries = GetSelectedEntries(
      getSelectedUIDsFromPath(this.props.match.params),
      this.state.filteredReport.report
    );

    if (selectedEntries.length) {
      window.document.title = `${_.last(selectedEntries).name} | \
                               ${selectedEntries
                                 .slice(0, -1)
                                 .map((entry) => entry.name)
                                 .join(" > ")}`;
    }

    const centerPane = GetCenterPane(
      this.state,
      reportFetchMessage,
      this.props.match.params.uid,
      selectedEntries
    );

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          filterBoxWidth={this.state.navWidth}
          filterText={this.state.filteredReport.filter.text}
          status={reportStatus}
          report={this.state.report}
          expandStatus={this.state.assertionStatus.globalExpand.status}
          updateExpandStatusFunc={this.updateGlobalExpand}
          handleNavFilter={this.handleNavFilter}
          updateFilterFunc={this.updateFilter}
          updateEmptyDisplayFunc={this.updateDisplayEmpty}
          updateTreeViewFunc={this.updateTreeView}
          updateTagsDisplayFunc={this.updateTagsDisplay}
          updatePathDisplayFunc={this.updatePathDisplay}
          updateTimeDisplayFunc={this.updateTimeDisplay}
        />
        <NavBreadcrumbs entries={selectedEntries} url={this.props.match.path} />
        <div
          style={{
            display: "flex",
            flex: "1",
            overflowY: "auto",
          }}
        >
          <Nav
            interactive={false}
            navListWidth={this.state.navWidth}
            report={this.state.filteredReport.report}
            selected={selectedEntries}
            filter={this.state.filter}
            treeView={this.state.treeView}
            displayEmpty={this.state.displayEmpty}
            displayTags={this.state.displayTags}
            displayTime={this.state.displayTime}
            handleColumnResizing={this.handleColumnResizing}
            url={this.props.match.path}
          />
          <AssertionContext.Provider value={this.state.assertionStatus}>
            {centerPane}
          </AssertionContext.Provider>
        </div>
      </div>
    );
  }
}

BatchReport.propTypes = {
  match: PropTypes.object,
};

const styles = StyleSheet.create({
  batchReport: {
    /** overflow will hide dropdown div */
    // overflow: 'hidden'
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
});

export default BatchReport;
