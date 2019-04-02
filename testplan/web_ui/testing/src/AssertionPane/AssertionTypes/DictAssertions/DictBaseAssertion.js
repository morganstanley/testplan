import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import {AgGridReact} from 'ag-grid-react';

import {
  calculateDictGridHeight,
} from './dictAssertionUtils';


/**
 * Base assertion that are used to render dict-like data.
 * It renders the cells with the following content:
 * 
 * {Buttons}
 * {Ag-Grid Table}
 * 
 */
class DictBaseAssertion extends Component {
  constructor(props) {
    super(props);

    this.onGridReady = this.onGridReady.bind(this);
  }

  /**
   * Resize the columns of the grid if the component updated.
   * @public
   */
  componentDidUpdate() {
    this.sizeToFit();
  }

  /**
   * Handler for the grid's onGridReady event. The grid's API is loaded and the
   * columns are resized.
   * @param params
   * @public
   */
  onGridReady(params) {
    this.gridApi = params.api;
    this.gridColumnApi = params.columnApi;
    this.sizeToFit();
  }

  /**
   * Resize every column to take up all the available space but do not exceed
   * the width of the grid.
   * @public
   */
  sizeToFit() {
    if (this.gridApi) this.gridApi.sizeColumnsToFit();
  }

  render() {
    const normalRows = this.props.rowData.filter(
      row => !row.descriptor.isEmptyLine).length;
    const emptyRows = this.props.rowData.filter(
      row => row.descriptor.isEmptyLine).length;
    const height = calculateDictGridHeight(normalRows, emptyRows);

    return (
      <Fragment>
        {this.props.buttonGroup}
        <div
          className={
            `ag-theme-balham ${css(styles.isResizable)} ${css(styles.gridFont)}`
          }
          style={{ height: `${height}px` }}
        >
          <AgGridReact
            animateRows={true}
            enableColResize={true}
            onGridReady={this.onGridReady}
            columnDefs={this.props.columnDefs}
            rowData={this.props.rowData}
            getRowHeight={
              (params) => params.data.descriptor.isEmptyLine ? 5 : 28
            }
          />
        </div>
      </Fragment>
    );
  }
}

DictBaseAssertion.propTypes = {
  /** The group of button will be display on the top of table */
  buttonGroup: PropTypes.object,
  /** The head data of ag-grid */
  columnDefs: PropTypes.array.isRequired,
  /** The row data of ag-grid */
  rowData: PropTypes.array.isRequired,
};

const styles = StyleSheet.create({
  gridFont: {
    fontSize: '13px',
    fontFamily: 'monospace',
  },

  isResizable: {
    overflow: 'hidden',
    resize: 'vertical',
    paddingBottom: '1rem',
    minHeight: '100px',
  },
});


export default DictBaseAssertion;