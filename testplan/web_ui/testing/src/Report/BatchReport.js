import React from 'react';
import {StyleSheet, css} from 'aphrodite';
import axios from 'axios';

import Toolbar from '../Toolbar/Toolbar';
import Nav from '../Nav/Nav';
import {
  PropagateIndices,
  UpdateSelectedState,
  GetReportState,
  GetCenterPane,
  GetSelectedEntries,
} from "./reportUtils";
import {COLUMN_WIDTH} from "../Common/defaults";
import {fakeReportAssertions} from "../Common/fakeReport";

/**
 * BatchReport component:
 *   * fetch Testplan report.
 *   * display messages when loading report or error in report.
 *   * render toolbar, nav & assertion components.
 */
class BatchReport extends React.Component {
  constructor(props) {
    super(props);
    this.handleNavFilter = this.handleNavFilter.bind(this);
    this.updateFilter = this.updateFilter.bind(this);
    this.updateTagsDisplay = this.updateTagsDisplay.bind(this);
    this.updateDisplayEmpty = this.updateDisplayEmpty.bind(this);
    this.handleNavClick = this.handleNavClick.bind(this);

    this.state = {
      navWidth: COLUMN_WIDTH,
      report: null,
      testcaseUid: null,
      loading: false,
      error: null,
      filter: null,
      displayTags: false,
      displayEmpty: true,
      selectedUIDs: [],
    };
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
      const processedReport = PropagateIndices(fakeReportAssertions);
      setTimeout(
        () => this.setState({
          report: processedReport,
          selectedUIDs: this.autoSelect(processedReport),
          loading: false,
        }),
        1500);
    } else {
      axios.get(`/api/v1/reports/${uid}`)
        .then(response => {
          const processedReport = PropagateIndices(response.data);
          this.setState({
            report: processedReport,
            selectedUIDs: this.autoSelect(processedReport),
            loading: false,
          });
        })
        .catch(error => this.setState({
          error: error,
          loading: false,
        }));
    }
  }

  /**
   * Auto-select an entry in the report when it is first loaded.
   * @param {reportNode} reportEntry - the current report entry to select from.
   * @return {Array[string]} List of UIDs of the currently selected entries.
   */
  autoSelect(reportEntry) {
    const selection = [reportEntry.uid];

    // If the current report entry has only one child entry and that entry is
    // not a testcase, we automatically expand it.
    if ((reportEntry.entries.length === 1) &&
        (reportEntry.entries[0].category!== "testcase")) {
      return selection.concat(this.autoSelect(reportEntry.entries[0]));
    } else {
      return selection;
    }
  }

  /**
   * Fetch the Testplan report once the component has mounted.
   * @public
   */
  componentDidMount() {
    this.setState({loading: true}, this.getReport);
  }

  /**
   * Handle filter expressions being typed into the filter box. Placeholder.
   *
   * @param {Object} e - keyup event.
   * @public
   */
  handleNavFilter(e) { // eslint-disable-line no-unused-vars
    // Save expressions to state.
  }

  /**
   * Update the global filter state of the entry.
   *
   * @param {string} filter - null, all, pass or fail.
   * @public
   */
  updateFilter(filter) {
    this.setState({filter: filter});
  }

  updateTagsDisplay(displayTags) {
    this.setState({displayTags: displayTags});
  }

  updateDisplayEmpty(displayEmpty) {
    this.setState({displayEmpty: displayEmpty});
  }

  /**
   * Handle a navigation entry being clicked.
   */
  handleNavClick(e, entry, depth) {
    e.stopPropagation();
    this.setState((state, props) => UpdateSelectedState(state, entry, depth));
  }

  render() {
    const {reportStatus, reportFetchMessage} = GetReportState(this.state);

    if (this.state.report && this.state.report.name) {
      window.document.title = this.state.report.name;
    }

    const selectedEntries = GetSelectedEntries(
      this.state.selectedUIDs, this.state.report
    );
    const centerPane = GetCenterPane(
      this.state,
      this.props,
      reportFetchMessage,
      this.props.match.params.uid,
      selectedEntries,
    );

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          status={reportStatus}
          report={this.state.report}
          handleNavFilter={this.handleNavFilter}
          updateFilterFunc={this.updateFilter}
          updateEmptyDisplayFunc={this.updateDisplayEmpty}
          updateTagsDisplayFunc={this.updateTagsDisplay}
        />
        <Nav
          report={this.state.report}
          selected={selectedEntries}
          filter={this.state.filter}
          displayEmpty={this.state.displayEmpty}
          displayTags={this.state.displayTags}
          handleNavClick={this.handleNavClick}
        />
        {centerPane}
      </div>
    );
  }
}

const styles = StyleSheet.create({
  batchReport: {
    /** overflow will hide dropdown div */
    // overflow: 'hidden'
  }
});

export default BatchReport;
