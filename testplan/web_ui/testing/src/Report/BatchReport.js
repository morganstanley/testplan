import React from 'react';
import { StyleSheet, css } from 'aphrodite';
import axios from 'axios';
import PropTypes from 'prop-types';

import { parseToJson } from "../Common/utils";
import Toolbar from '../Toolbar/Toolbar';
import { TimeButton } from '../Toolbar/Buttons';
import Nav from '../Nav/Nav';
import {
  PropagateIndices,
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
  MergeSplittedReport,
  filterReport,
  getSelectedUIDsFromPath,
} from "./reportUtils";
import { generateSelectionPath } from './path';

import { COLUMN_WIDTH } from "../Common/defaults";
import { fakeReportAssertions } from "../Common/fakeReport";

/**
 * BatchReport component:
 *   * fetch Testplan report.
 *   * display messages when loading report or error in report.
 *   * render toolbar, nav & assertion components.
 */
class BatchReport extends React.Component {

  constructor(props) {
    super(props);
    this.setError = this.setError.bind(this);
    this.setReport = this.setReport.bind(this);
    this.getReport = this.getReport.bind(this);
    this.handleNavFilter = this.handleNavFilter.bind(this);
    this.updateFilter = this.updateFilter.bind(this);
    this.updateTagsDisplay = this.updateTagsDisplay.bind(this);
    this.updateTimeDisplay = this.updateTimeDisplay.bind(this);
    this.updateDisplayEmpty = this.updateDisplayEmpty.bind(this);
    this.handleColumnResizing = this.handleColumnResizing.bind(this);

    this.state = {
      navWidth: `${COLUMN_WIDTH}em`,
      report: null,
      filteredReport: { filter: { text: null, filters: null }, report: null },
      testcaseUid: null,
      loading: false,
      error: null,
      filter: null,
      displayTags: false,
      displayTime: false,
      displayEmpty: true,
    };
  }

  setError(error) {
    console.log(error);
    this.setState({ error: error, loading: false });
  }

  setReport(report) {
    const processedReport = PropagateIndices(report);
    const filteredReport = filterReport(
      processedReport,
      this.state.filteredReport.filter);

    const redirectPath = this.props.match.params.selection ?
      null :
      generateSelectionPath(
        this.props.match.path,
        [filteredReport.report.uid]
      );

    this.setState({
      report: processedReport,
      filteredReport,
      loading: false,
    }, () => {
      if (redirectPath) {
        this.props.history.replace(redirectPath);
      }
    }
    );
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
    if (uid === "_dev") {
      var fakeReport = this.updateReportUID(fakeReportAssertions, uid);
      setTimeout(
        () => this.setReport(fakeReport),
        1500);
    } else {
      axios.get(`/api/v1/reports/${uid}`)
        .then(response => {
          const rawReport = response.data;
          if (rawReport.version === 2) {
            const assertionsReq = axios.get(
              `/api/v1/reports/${uid}/attachments/${rawReport.assertions_file}`,
              { transformResponse: parseToJson }
            );
            const structureReq = axios.get(
              `/api/v1/reports/${uid}/attachments/${rawReport.structure_file}`,
              { transformResponse: parseToJson }
            );
            axios.all([assertionsReq, structureReq]).then(
              axios.spread((assertionsRes, structureRes) => {
                if (!assertionsRes.data) {
                  alert(
                    "Failed to parse assertion datails!\n"
                    + "Please report this issue to the Testplan team."
                  );
                  console.error(assertionsRes);
                }
                const mergedReport = MergeSplittedReport(
                  rawReport, assertionsRes.data, structureRes.data
                );
                this.setReport(this.updateReportUID(mergedReport, uid));
              })
            ).catch(this.setError);
          } else {
            this.setReport(this.updateReportUID(rawReport, uid));
          }
        }).catch(this.setError);
    }
  }

  updateReportUID(report, uid) {
    return { ...report, uid };
  }

  /**
   * Fetch the Testplan report once the component has mounted.
   * @public
   */
  componentDidMount() {
    this.setState({ loading: true }, this.getReport);
  }

  /**
   * Handle filter expressions being typed into the filter box.
   *
   * @param {Object} filter - the paresed filter expression
   * @public
   */
  handleNavFilter(filter) { // eslint-disable-line no-unused-vars
    const filteredReport = filterReport(this.state.report, filter);

    this.setState({
      filteredReport,
    });
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

  /**
   * Update execution time display of each navigation entry and each assertion.
   *
   * @param {boolean} displayTime.
   * @public
   */
  updateTimeDisplay(displayTime) {
    this.setState({ displayTime: displayTime });
  }

  /**
   * Handle resizing event and update NavList & Center Pane.
   */
  handleColumnResizing(navWidth) {
    this.setState({ navWidth: navWidth });
  }

  getSelectedUIDsFromPath() {
    const { uid, selection } = this.props.match.params;
    return [uid, ...(selection ? selection.split('/') : [])];
  }

  selectionMatchPath(entries_selection) {
    let [uid, ...selection] =
      entries_selection[entries_selection.length - 1].uids;

    selection = selection.length ? selection.join("/") : undefined;

    return uid === this.props.match.params.uid &&
      selection === this.props.match.params.selection;
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

    const centerPane = GetCenterPane(
      this.state,
      reportFetchMessage,
      this.props.match.params.uid,
      selectedEntries,
    );

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          filterBoxWidth={this.state.navWidth}
          filterText={this.state.filteredReport.filter.text}
          status={reportStatus}
          report={this.state.report}
          handleNavFilter={this.handleNavFilter}
          updateFilterFunc={this.updateFilter}
          updateEmptyDisplayFunc={this.updateDisplayEmpty}
          updateTagsDisplayFunc={this.updateTagsDisplay}
          extraButtons={[<TimeButton
            key="time-button"
            status={reportStatus}
            updateTimeDisplayCbk={this.updateTimeDisplay}
          />]}
        />
        <Nav
          navListWidth={this.state.navWidth}
          report={this.state.filteredReport.report}
          selected={selectedEntries}
          filter={this.state.filter}
          displayEmpty={this.state.displayEmpty}
          displayTags={this.state.displayTags}
          displayTime={this.state.displayTime}
          handleColumnResizing={this.handleColumnResizing}
          url={this.props.match.path}
        />
        {centerPane}
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
  }
});

export default BatchReport;
