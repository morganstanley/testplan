import React from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableLogColumnDefs,
  prepareTableLogRowData,
} from './tableAssertionUtils';


/**
 * Component that are used to render TableLog assertion.
 */
export default function TableLogAssertion (props) {
  let columnDefs = prepareTableLogColumnDefs(props.assertion.columns);
  let rowData = prepareTableLogRowData(
    props.assertion.indices, 
    props.assertion.table,
    props.assertion.columns
  );

  return (
    <TableBaseAssertion
      columns={columnDefs}
      rows={rowData}
    />
  );
};


TableLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
