import React from 'react';
import PropTypes from 'prop-types';
import {library} from '@fortawesome/fontawesome-svg-core';
import {faInfoCircle} from '@fortawesome/free-solid-svg-icons';

import DictCellRenderer from './DictCellRenderer';
// import FixTagToolTip from './FixTagToolTip'

library.add(faInfoCircle);


/**
 * Custom cell renderer component used by FixLog and FixMatch assertions.
 *
 * It renders the cells with the following content:
 *
 * {icon} {mainText} {subText}
 *
 * Where:
 *  - icon is an info logo for FIX keys,
 *  - mainText is the main data of the cell, it can be a key or a value,
 *  - subText is the type of the value in subscript and
 */
export default function FixCellRenderer(props) {
  if (!props.data) {
    return null;
  }

  const lineNo = props.data.descriptor.lineNo;
  const rowIndex = props.rowIndex;
  const colField = props.colDef.field;
  const toolTipId = `id_${lineNo}_${rowIndex}_${colField}`;

  return (
    <>
      <DictCellRenderer
        id={toolTipId}
        data={props.data}
        value={props.value}
        colDef={props.colDef}
      />
    </>
  );
}


FixCellRenderer.propTypes = {
  /** The meta info of current cell */
  data: PropTypes.object,
  /** The row index of the current cell */
  rowIndex: PropTypes.number,
  /** The Column definition of the current cell */
  colDef: PropTypes.object,
};
