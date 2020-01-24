import React, {Component} from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableColumnDefs,
  prepareTableRowData,
} from './tableAssertionUtils';


/**
 * Component that are used to render TableMatch assertion.
 */
class TableMatchAssertion extends Component {
  render() {
    let columnDefs = prepareTableColumnDefs(this.props.assertion.columns);
    let rowData = prepareTableRowData(
      this.props.assertion.data, 
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

TableMatchAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default TableMatchAssertion;