import React, {Component} from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableLogColumnDefs,
  prepareTableLogRowData,
} from './tableAssertionUtils';


/**
 * Component that are used to render TableLog assertion.
 */
class TableLogAssertion extends Component {
  render() {
    let columnDefs = prepareTableLogColumnDefs(this.props.assertion.columns);
    let rowData = prepareTableLogRowData(
      this.props.assertion.indices, 
      this.props.assertion.table,
      this.props.assertion.columns
    );
    return (
      <TableBaseAssertion
        columnDefs={columnDefs}
        rowData={rowData}
      />
    );
  }
}

TableLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default TableLogAssertion;