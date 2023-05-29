import React from "react";
import PropTypes from "prop-types";
import TableBaseAssertion from "./TableBaseAssertion";

import {
  prepareTableMatchColumnDefs,
  prepareTableRowData,
} from "./tableAssertionUtils";

/**
 * Component that are used to render TableMatch assertion.
 */
export default function TableMatchAssertion(props) {
  let columns = prepareTableMatchColumnDefs(
    props.assertion.columns,
    props.assertion.include_columns,
    props.assertion.exclude_columns
  );
  let rows = prepareTableRowData(props.assertion.data, props.assertion.columns);

  return <TableBaseAssertion columns={columns} rows={rows} />;
}

TableMatchAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
