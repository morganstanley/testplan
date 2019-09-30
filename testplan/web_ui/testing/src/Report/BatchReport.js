import React, {Component} from 'react';
import {StyleSheet, css} from 'aphrodite';
import axios from 'axios';

import Toolbar from '../Toolbar/Toolbar';
import Nav from '../Nav/Nav';
import AssertionPane from '../AssertionPane/AssertionPane';
import Message from '../Common/Message';
import {propagateIndices} from "./reportUtils";
import {COLUMN_WIDTH} from "../Common/defaults";
import {getNavEntryType} from "../Common/utils";
import {fakeReportAssertions} from "../Common/fakeReport";

/**
 * BatchReport component:
 *   * fetch Testplan report.
 *   * display messages when loading report or error in report.
 *   * render toolbar, nav & assertion components.
 */
class BatchReport extends Component {
  constructor(props) {
    super(props);
    this.saveAssertions = this.saveAssertions.bind(this);
    this.handleNavFilter = this.handleNavFilter.bind(this);
    this.updateFilter = this.updateFilter.bind(this);
    this.updateTagsDisplay = this.updateTagsDisplay.bind(this);
    this.updateDisplayEmpty = this.updateDisplayEmpty.bind(this);

    this.state = {
      navWidth: COLUMN_WIDTH,
      report: undefined,
      assertions: undefined,
      testcaseUid: undefined,
      loading: false,
      error: undefined,
      filter: undefined,
      displayTags: false,
      displayEmpty: true,
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
      const r = propagateIndices([fakeReportAssertions]);
      setTimeout(() => {this.setState({report: r, loading: false});}, 1500);
    } else {
      axios.get(`/api/v1/reports/${uid}`)
        .then(response => propagateIndices([response.data]))
        .then(report => this.setState({
          report: report,
          selected: [{uid: report[0].uid, type: 'testplan'}],
          loading: false
        }))
        .catch(error => this.setState({
          error,
          loading: false
        }));
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
   * Set or clear the assertions in state depending on the type of the entry.
   *
   * @param {Object} entry - current entry clicked on the Nav.
   * @public
   */
  saveAssertions(entry) {
    const entryType = getNavEntryType(entry);
    if (entryType === 'testcase') {
      this.setState({assertions: entry.entries, testcaseUid: entry.uid});
    } else {
      this.setState({assertions: undefined, testcaseUid: undefined});
    }
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
   * @param {string} filter - undefined, all, pass or fail.
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

  render() {
    let report = [];
    let reportStatus;
    let reportFetchMessage;

    // Handle the Testplan report if it has been fetched.
    if (this.state.report === undefined) {
      // The Testplan report hasn't been fetched yet.
      if (this.state.loading) {
        reportFetchMessage = 'Fetching Testplan report...';
      } else if (this.state.error !== undefined){
        reportFetchMessage = 'Error fetching Testplan report. ' +
        `(${this.state.error.message})`;
      } else {
        reportFetchMessage = 'Waiting to fetch Testplan report...';
      }
    } else {
      // The Testplan report has been fetched.
      reportStatus = this.state.report[0].status;
      report = this.state.report;
    }

    // Create the center pane.
    let centerPane;
    if (this.state.assertions !== undefined) {
      centerPane = <AssertionPane
        assertions={this.state.assertions}
        left={this.state.navWidth + 1.5}
        testcaseUid={this.state.testcaseUid}
        filter={this.state.filter}
        reportUid={this.props.match.params.uid}
      />;
    } else if (reportFetchMessage !== undefined) {
      centerPane = <Message
        message={reportFetchMessage}
        left={this.state.navWidth} />;
    } else {
      centerPane = <Message
        message='Please select a testcase.'
        left={this.state.navWidth} />;
    }

    return (
      <div className={css(styles.batchReport)}>
        <Toolbar
          status={reportStatus}
          handleNavFilter={this.handleNavFilter}
          updateFilterFunc={this.updateFilter}
          updateEmptyDisplayFunc={this.updateDisplayEmpty}
          updateTagsDisplayFunc={this.updateTagsDisplay}
        />
        <Nav
          report={report}
          saveAssertions={this.saveAssertions}
          filter={this.state.filter}
          displayEmpty={this.state.displayEmpty}
          displayTags={this.state.displayTags}
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
