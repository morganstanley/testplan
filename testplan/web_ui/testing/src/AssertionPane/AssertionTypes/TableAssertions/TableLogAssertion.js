import React from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableColumn,
  prepareTableLogRowData,
} from './tableAssertionUtils';


/**
 * Component that are used to render TableLog assertion.
 */
export default function TableLogAssertion (props) {
  let columns = prepareTableColumn(props.assertion.columns);
  let rows = prepareTableLogRowData(
    props.assertion.indices, 
    props.assertion.table,
    props.assertion.columns
  );
  return (
    <TableBaseAssertion columns={columns} rows={rows}/>
  );
};

TableLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
