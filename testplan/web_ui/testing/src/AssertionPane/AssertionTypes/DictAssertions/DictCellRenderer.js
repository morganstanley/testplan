import React from 'react';
import PropTypes from 'prop-types';
import { INDENT_MULTIPLIER } from './../../../Common/defaults';

/**
 * Custom cell renderer component used by DictLog and DictMatch assertions.
 *
 * It renders the cells with the following content:
 *
 * {icon} {mainText} {subText}
 *
 * Where:
 *  - icon is an info logo for custom,
 *  - mainText is the main data of the cell, it can be a key or a value,
 *  - subText is the type of the value in subscript and
 */
export default function DictCellRenderer(props) {
  let mainText = null;
  let subText = null;
  let indentStyle = {};
  if (props.field === 'key') {
    if (props.data.key) {
      mainText = props.data.key.value;
    } else {
      return null;
    }

    if (mainText && props.data.descriptor.isListKey) {
      subText = 'list';
    }

    if (props.data.descriptor.indent) {
      const indent = props.data.descriptor.indent * INDENT_MULTIPLIER;
      indentStyle.marginLeft = `${indent}rem`;
    }

  } else {  // Cell is value/expect column.
    if (props.data[props.field]) {
      mainText = props.data[props.field].value;
      subText = props.data[props.field].type;
    } else {
      return null;
    }
  }

  if (props.data.descriptor.status === 'Failed') {
    indentStyle.color = 'red';
  }

  return (
    <div style={indentStyle}>
      <span
        style={{userSelect: 'all'}}
        id={props.id}
        onMouseEnter={props.onMouseEnter}
        onMouseLeave={props.onMouseLeave}
      >
        {mainText}
      </span>
      <sub>{subText}</sub>
    </div>
  );
}


DictCellRenderer.propTypes = {
  /** The meta info of current row. */
  data: PropTypes.object,
  /** The info logo for FIX keys, */
  icon: PropTypes.object,
  /** ID of the cell being rendered. */
  id: PropTypes.string,
  /** Function to call when mouse enters cell. */
  onMouseEnter: PropTypes.func,
  /** Function to call when mouse leaves cell. */
  onMouseLeave: PropTypes.func,
  /** Column field */
  field: PropTypes.string,
};
