import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Assertion from './Assertion';

/**
 * A component that wraps the rendered assertions. It is also the point where
 * recursion begins for grouped assertions.
 */
class AssertionGroup extends Component {
  render() {
    return this.props.entries.filter((assertion) => {
      if (this.props.filter === 'pass') {
        // Log assertion will be displayed
        if (assertion.passed === false) return false;
      } else if (this.props.filter === 'fail') {
        // Log assertion will be displayed
        if (assertion.passed === true) return false;
      }
      return true;
    }).map((assertion, index) =>
      <Assertion
        key={'assertion_' + index}
        assertion={assertion}
        globalIsOpen={this.props.globalIsOpen}
        resetGlobalIsOpen={this.props.resetGlobalIsOpen}
        index={index}
        filter={this.props.filter}
        reportUid={this.props.reportUid}
      />
    );
  }
}

AssertionGroup.propTypes = {
  /** Array of assertions to be rendered */
  entries: PropTypes.arrayOf(PropTypes.object),
  /** State of the expand all/collapse all functionality */
  globalIsOpen: PropTypes.bool,
  /** Function to reset the expand all/collapse all state if an individual
   * assertion's visibility is changed */
  resetGlobalIsOpen: PropTypes.func,
  /** Assertion filter */
  filter: PropTypes.string,
  /** ReportUid */
  reportUid: PropTypes.string,
};

export default AssertionGroup;
