import React, {Component, Fragment} from 'react';
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
export default class FixCellRenderer extends Component {
  constructor(props) {
    super(props);

    this.onMouseEnter = this.onMouseEnter.bind(this);
    this.onMouseLeave = this.onMouseLeave.bind(this);

    this.tooltip = React.createRef();
  }

  /**
   * Event handler to activate tooltips.
   */
  onMouseEnter() {
    if (this.tooltip.current !== null)
      this.tooltip.current.showTooltip();
  }

  /**
   * Event handler to deactivate tooltips.
   */
  onMouseLeave() {
    if (this.tooltip.current !== null)
      this.tooltip.current.hideTooltip();
  }

  render() {
    if (!this.props.data) {
      return null;
    }

    const lineNo = this.props.data.descriptor.lineNo;
    const rowIndex = this.props.rowIndex;
    const colField = this.props.field;
    const toolTipId = `id_${lineNo}_${rowIndex}_${colField}`;

    return (
      <Fragment>
        <DictCellRenderer
          id={toolTipId}
          data={this.props.data}
          field={this.props.field}
          onMouseEnter={this.onMouseEnter}
          onMouseLeave={this.onMouseLeave}
        />
        {/*<FixTagToolTip*/}
          {/*parent={`#${toolTipId}`}*/}
          {/*cellValue={this.props.value.value}*/}
          {/*keyValue={this.props.data.key.value}*/}
          {/*colField={colField}*/}
          {/*ref={this.tooltip}*/}
        {/*/>*/}
      </Fragment>
    );
  }
}


FixCellRenderer.propTypes = {
  /** The meta info of current cell */
  data: PropTypes.object,
  /** The row index of the current cell */
  rowIndex: PropTypes.number,
  /** The Column definition of the current cell */
  field: PropTypes.string,
};
