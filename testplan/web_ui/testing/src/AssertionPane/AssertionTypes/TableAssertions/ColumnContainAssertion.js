import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableColumnContainDefs,
  prepareTableColumnContainRowData,
  prepareTableColumnContainPreText
} from './tableAssertionUtils';


/**
 * Component that are used to render ColumnContain assertion.
 */
class ColumnContainAssertion extends Component {
  constructor(props) {
    super(props);

    this.columnDefs = prepareTableColumnContainDefs(
      this.props.assertion.column);
    this.rowData = prepareTableColumnContainRowData(
      this.props.assertion.data, this.props.assertion.values);
  }

  render() {
    let preText = (
      <Fragment>
        Values: [{
          prepareTableColumnContainPreText(this.props.assertion.values)
        }]
      </Fragment>
    );

    return (
      <TableBaseAssertion
        columnDefs={this.columnDefs}
        rowData={this.rowData}
        preText={preText}
      />
    );
  }
}

ColumnContainAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default ColumnContainAssertion;