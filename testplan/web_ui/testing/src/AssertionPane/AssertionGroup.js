import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Assertion from './Assertion';

/**
 * A component that wraps the rendered assertions. It is also the point where
 * recursion begins for grouped assertions.
 */
class AssertionGroup extends Component {
  render() {
    return this.props.entries.map((assertion, index) =>
      <Assertion
        key={'assertion_' + index}
        assertion={assertion}
        globalIsOpen={this.props.globalIsOpen}
        resetGlobalIsOpen={this.props.resetGlobalIsOpen}
        index={index}
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
};

export default AssertionGroup;