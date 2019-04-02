import React, {Component} from 'react';
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
class DictCellRenderer extends Component {
  render() {
    if (!this.props.value) {
      return null;
    }

    let mainText = this.props.value.value;

    let subText;
    let cellStyle;
    if (this.props.colDef.field === 'key') {
      if (this.props.data.descriptor.isListKey && mainText) {
        subText = 'list';
      }

      if (this.props.data.descriptor.indent) {
        const indent = this.props.data.descriptor.indent * INDENT_MULTIPLIER;
        cellStyle = {marginLeft: `${indent}rem`};
      }
    } else {
      subText = this.props.value.type;
    }

    return (
      <div style={cellStyle}>
        <span
          id={this.props.id}
          onMouseEnter={this.props.onMouseEnter}
          onMouseLeave={this.props.onMouseLeave}
        >
          {mainText}<sub>{subText}</sub>
        </span>
      </div>
    );
  }
}


DictCellRenderer.propTypes = {
  /** The data of current cell. */
  value: PropTypes.object,
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
  /** Ag-Grid colDef property */
  colDef: PropTypes.object,
};


export default DictCellRenderer;
