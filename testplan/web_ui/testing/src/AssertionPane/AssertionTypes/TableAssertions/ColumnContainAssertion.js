import React, {Fragment} from 'react';
import PropTypes from 'prop-types';
import TableBaseAssertion from './TableBaseAssertion';

import {
  prepareTableColumnContainColumn,
  prepareTableColumnContainRowData,
  prepareTableColumnContainPreText
} from './tableAssertionUtils';


/**
 * Component that are used to render ColumnContain assertion.
 */

export default function ColumnContainAssertion (props) {
  let columns = prepareTableColumnContainColumn(
    props.assertion.column
  );
  let rows = prepareTableColumnContainRowData(
    props.assertion.data,
    props.assertion.values
  );

  let preText = (
    <Fragment>
      Values: [{
        prepareTableColumnContainPreText(props.assertion.values)
      }]
    </Fragment>
  );

  return (
    <TableBaseAssertion
      columns={columns}
      rows={rows}
      preText={preText}
    />
  );
};


ColumnContainAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
